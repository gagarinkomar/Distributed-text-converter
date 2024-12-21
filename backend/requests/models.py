import uuid
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile

import datetime
from django.utils import timezone

from requests.storage_backends import UploadedStorage, EditedStorage, ResultStorage

RESULT_STORAGE = ResultStorage()


class RequestStatus(models.TextChoices):
    WAITING = 'waiting', 'Waiting'
    PROCESSING = 'processing', 'Processing'
    DONE = 'done', 'Done'


class Request(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=RequestStatus.choices,
                              default=RequestStatus.WAITING)
    time_end = models.DateTimeField(null=True, blank=True)
    url = models.CharField(max_length=250, blank=True, null=True)
    file = models.FileField(storage=RESULT_STORAGE)
    expiration_date = models.DateTimeField(null=True, blank=True)

    @classmethod
    def create_request(cls):
        return cls.objects.create()

    @classmethod
    def get_request(cls, request_id: str):
        return cls.objects.get(id=request_id)

    @classmethod
    def is_request_done(cls, request_id: str):
        request = cls.objects.get(id=request_id)
        return not request is None and request.status == RequestStatus.DONE

    def get_resulting_link(self, expiration=3600):
        if not self.status == RequestStatus.DONE:
            raise ValueError("Task is not done!")
        if not self.file:
            raise BrokenPipeError("There should be file if task is done")
        if self.url:
            return self.url

        s3_client = RESULT_STORAGE.connection.meta.client
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket_name,
                'Key': f"{ResultStorage.location}/{self.id}.zip",
            },
            ExpiresIn=expiration
        )
        url = url[url.index('//') + 2:]
        url = url[url.index('/'):]
        url = '/minio' + url
        self.url = url
        self.save()
        return url
    
    def update_file(self, name: str, data):
        self.file = ContentFile(data, name=name)
        self.save()
        

    def update_expiration_date(self):
        self.expiration_date = timezone.now() + timezone.timedelta(hours=1)
        self.save()
        
    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save=False)
            
        uploaded_files = UploadedFile.objects.filter(request=self)
        for uploaded_file in uploaded_files:
            uploaded_file.delete()
            
        edited_files = EditedFile.objects.filter(request=self)
        for edited_file in edited_files:
            edited_file.delete()
        
        super().delete(*args, **kwargs)
    
    def update_status_done(self):
        self.status = RequestStatus.DONE
        self.save()

    def __str__(self):
        return str(self.id) + " — " + str(self.status)


class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)

    @classmethod
    def get_by_id(cls, id):
        return cls.objects.get(id=id)
    
    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True


class UploadedFile(File):
    status = models.CharField(max_length=10, choices=RequestStatus.choices,
                              default=RequestStatus.WAITING)
    uploaded_name = models.CharField(max_length=100)

    file = models.FileField(storage=UploadedStorage())

    def get_file_data(self):
        with self.file.file.open('rb') as f:
            return f.read()

    @classmethod
    def create_file(cls, request: Request, uploaded_name: str, file):
        id = uuid.uuid4()
        file.name = str(id) + "." + uploaded_name.split('.')[-1]

        return cls.objects.create(id=id, request=request, uploaded_name=uploaded_name, file=file)


class EditedFile(File):
    file = models.FileField(storage=EditedStorage())

    @classmethod
    def create_file(cls, request: Request, name: str, data):
        file = ContentFile(data, name=name)

        return cls.objects.create(request=request, file=file)
    
    def get_file_data(self):
        with self.file.file.open('rb') as f:
            return f.read()
