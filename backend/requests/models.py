from django.db import models
import uuid
from requests.storage_backends import PublicMediaStorage


# class Request(models.Model):
#     test_field = models.IntegerField()
#
#     def __str__(self):
#         return str(self.test_field)


class Upload(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(storage=PublicMediaStorage())

class RequestStatus(models.TextChoices):
    WAITING = 'waiting', 'Waiting'
    PROCESSING = 'processing', 'Processing'
    DONE = 'done', 'Done'

class Request(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=RequestStatus.choices, default=RequestStatus.WAITING)
    time_end = models.DateTimeField(null=True, blank=True)

    @classmethod
    def create_request(cls):
        return cls.objects.create()

    def __str__(self):
        return str(self.id) + " — " + str(self.status)

class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=RequestStatus.choices, default=RequestStatus.WAITING)
    request = models.ForeignKey(Request, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default=uuid.uuid4)

    @classmethod
    def create_file(cls, request: Request, name: str):
        return cls.objects.create(request=request, name=name)
