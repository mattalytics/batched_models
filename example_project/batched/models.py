from __future__ import unicode_literals

from django.db import models
from batched_models import BulkManager

class bulker(models.Model):
    id=models.AutoField(primary_key=True)
    x=models.TextField(unique=True)
    y=models.TextField()
    num = models.IntegerField(null=True)

    objects = BulkManager(500)