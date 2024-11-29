from django.db import models

class BaseModel(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Path(BaseModel):
    platform_id = models.IntegerField(null=False, blank=False)
    title = models.CharField(max_length=500, null=False, blank=False)
    progression = models.FloatField(default=0.0, null=False, blank=False)
    score = models.FloatField(default=0.0, null=False, blank=False)

    def __str__(self):
        return self.title


class Training(BaseModel):
    platform_id = models.IntegerField(null=False, blank=False)
    path = models.ForeignKey(Path, related_name='trainings', on_delete=models.CASCADE, null=False, blank=False)
    title = models.CharField(max_length=500, null=False, blank=False)
    progression = models.FloatField(default=0.0, null=False)
    score = models.FloatField(null=True, default=None)
    type = models.CharField(max_length=500, null=False, blank=False)
    def __str__(self):
        return self.title


class Step(BaseModel):
    platform_id = models.IntegerField(null=False, blank=False)
    training = models.ForeignKey(Training, related_name='steps', on_delete=models.CASCADE, null=False, blank=False)
    title = models.CharField(max_length=500, null=False, blank=False)
    type = models.CharField(max_length=500, null=False, blank=False)
    is_validated = models.BooleanField(default=False, null=False, blank=False)
    is_blocked = models.BooleanField(default=False, null=False, blank=False)
