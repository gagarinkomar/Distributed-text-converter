import boto3
from django.conf import settings
from django.http import HttpResponse

from django.shortcuts import render, get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Request, File, Upload
from tasks import task1, task2

from django.views.generic.edit import FormView
from .forms import FileFieldForm
from django.core.files.storage import FileSystemStorage



class RequestView(APIView):
    def get(self, request):
        requests = Request.objects.all()
        return Response({"requests": [str(request) for request in requests]})


class TestingView(APIView):
    def get(self, request):
        requests = Request.objects.all()
        return Response({"requests": [str(request) for request in requests]})

    def post(self, request):
        task_number = int(request.data.get('task_number'))
        number = int(request.data.get('number'))

        if task_number == 1:
            task1.delay(number)
        
        if task_number == 2:
            request_id = int(request.data.get('request_id'))
            file_id = int(request.data.get('file_id'))
            task2.delay(request_id, file_id)

        return Response({"success": f'Task with number {task_number} started'})


def image_upload(request):
    if request.method == 'POST':
        image_file = request.FILES['image_file']
        upload = Upload(file=image_file)
        upload.save()
        image_url = upload.file.url
        return render(request, 'upload.html', {
            'image_url': image_url
        })
    return render(request, 'upload.html')


def download_file(file_name):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL
    )
    try:
        response = s3_client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=settings.PUBLIC_MEDIA_LOCATION + '/' + file_name)
        file_content = response['Body'].read()
        return file_content
    except Exception as e:
        print(f"Ошибка загрузки файла: {e}")
        return None

def get_uploaded_file(request, file_id=1):
    upload = get_object_or_404(Upload, id=file_id)
    file_content = download_file(upload.file.name)

    if file_content:
        return HttpResponse(file_content, content_type='application/octet-stream')
    else:
        return HttpResponse("Файл не найден или произошла ошибка при загрузке.", status=404)
    
def handle_uploaded_file(file):
    fs = FileSystemStorage(location=settings.MEDIA_ROOT / 'uploads/')
    filename = fs.save(file.name, file)
    return fs.url(filename)

class FileFieldFormView(FormView):
    form_class = FileFieldForm
    template_name = "upload_images.html"  # Replace with your template.
    success_url = "/"  # Replace with your URL or reverse().

    def form_valid(self, form):
        files = form.cleaned_data["file_field"]
        request = Request.create_request()
        for file in files:
            if file.name.endswith('.jpg') or file.name.endswith('.png'):
                file_object = File.create_file(request, file.name)
                file.name = str(file_object.id) + "." + file.name.split('.')[-1]
                upload = Upload(file=file)
                upload.save()
            else:
                print("Not an image")
        self.success_url = f"/request/{str(request.id)}"
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
