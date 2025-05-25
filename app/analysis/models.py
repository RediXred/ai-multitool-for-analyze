from django.db import models
from django.contrib.auth.models import User
import os
from uuid import uuid4


import os
from uuid import uuid4

def user_directory_path(instance, filename):
    base, ext = os.path.splitext(filename)
    filename = f"{base}{ext}"
    return f"uploads/user_{instance.user.id}/{filename}"


# Create your models here.
class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files', null=True)
    file = models.FileField(upload_to=user_directory_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    analyzed = models.BooleanField(default=False)
    result = models.JSONField(blank=True, null=True)
    vt_result = models.JSONField(blank=True, null=True)
    vt_status = models.CharField(max_length=20, default='not_started')

    def __str__(self):
        return f"{self.user.username} - {self.file.name}"
    
    def filename(self):
        return os.path.basename(self.file.name)