from requests.models import Request, UploadedFile, EditedFile
from time import sleep
from requests.cutom_image_handler import ImageHandler

import zipfile
from io import BytesIO

from django.utils import timezone

from backend.celery import app

@app.task
def task_image_edit(file_id):
    image = UploadedFile.get_by_id(file_id)

    image_handler = ImageHandler()
    
    edited_image = image_handler.edit(image.get_file_data())

    file = EditedFile.create_file(image.request, image.uploaded_name, edited_image)

    return file.id

@app.task
def task_to_zip(file_ids):
    
    buffer_archive = BytesIO()
    with zipfile.ZipFile(buffer_archive, 'w') as archive:
        for file_id in file_ids:
            file = EditedFile.get_by_id(file_id)
            buffer_file = file.get_file_data()
            archive.writestr(file.file.name, buffer_file)
    buffer_archive.seek(0)
    
    file_example = EditedFile.get_by_id(file_ids[0])
    
    file_example.request.update_file(str(file_example.request.id) + '.zip', buffer_archive.getvalue())
    file_example.request.update_status_done()
    
    file_example.request.update_expiration_date()

    return True

@app.task
def task_clear_requests():
    print(timezone.now())
    requests = Request.objects.all()
    for request in requests:
        if request.expiration_date < timezone.now():
            uploaded_files = UploadedFile.objects.filter(request=request)
            for uploaded_file in uploaded_files:
                uploaded_file.delete_file()

            edited_files = EditedFile.objects.filter(request=request)
            for edited_file in edited_files:
                edited_file.delete_file()
                
            request.delete_file()
            request.delete()
        
    return True