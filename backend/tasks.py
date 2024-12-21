from requests.models import Request, UploadedFile, EditedFile
from time import sleep
from requests.cutom_image_handler import ImageHandler

import zipfile
from io import BytesIO

from backend.celery import app


@app.task
def task_image_edit(file_id):
    try:
        image = UploadedFile.get_by_id(file_id)

        image_handler = ImageHandler()

        edited_image = image_handler.edit(image.get_file_data())

        file = EditedFile.create_file(image.request, image.uploaded_name, edited_image)
    except Exception:
        return file_id, False
    
    return file.id, True


@app.task
def task_to_zip(file_ids):
    example_id = None

    buffer_archive = BytesIO()
    with zipfile.ZipFile(buffer_archive, 'w') as archive:
        for file_id, is_edited in file_ids:
            if not is_edited:
                continue

            example_id = file_id
            file = EditedFile.get_by_id(file_id)
            buffer_file = file.get_file_data()
            archive.writestr(file.file.name, buffer_file)
    buffer_archive.seek(0)

    if example_id is None:
        task_clear_request.delay(UploadedFile.get_by_id(file_ids[0][0]).request.id)
        return False

    file_1 = EditedFile.get_by_id(example_id)

    file_1.request.update_file(str(file_1.request.id) + '.zip', buffer_archive.getvalue())
    file_1.request.update_status_done()

    return True


@app.task
def task_clear_request(request_id):
    request = Request.objects.get(id=request_id)
    request.delete()

    return True
