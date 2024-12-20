import boto3
from django.conf import settings
from django.http import HttpResponse, JsonResponse

from django.shortcuts import render, get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Request, UploadedFile, UploadedFile, EditedFile
from tasks import task1, task2

from django.views.generic.edit import FormView
from .forms import FileFieldForm
from django.core.files.storage import FileSystemStorage


class TestingView(APIView):
    def get(self, request):
        requests = Request.objects.all()
        return Response({"requests": [str(request) for request in requests]})

    def post(self, request):
        file_id = request.data.get('file_id')
        task2.delay(file_id)

        return Response({"success": f'Task with number {123123} started'})


def get_task_status(request_id):
    return True


def request_status(request, request_id):
    return render(request, 'request.html', {'request_id': request_id})


def check_status(request, request_id):
    status = get_task_status(request_id)
    if status:
        return JsonResponse({'status': 'ready', 'link': f'/media/{request_id}_result.zip'})
    return JsonResponse({'status': 'pending'})


class FileFieldFormView(FormView):
    form_class = FileFieldForm
    template_name = "upload_images.html"
    success_url = "/"

    def form_valid(self, form):
        files = form.cleaned_data["file_field"]
        request = Request.create_request()
        for file in files:
            if file.name.endswith('.jpg') or file.name.endswith('.png'):
                UploadedFile.create_file(request, file.name, file)
            else:
                print("Not an image")
        self.success_url = f"/request/{str(request.id)}"
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
