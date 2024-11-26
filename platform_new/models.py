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
    path = models.ForeignKey(Path, on_delete=models.CASCADE, null=False, blank=False)
    title = models.CharField(max_length=500, null=False, blank=False)
    progression = models.FloatField(default=0.0, null=False)
    score = models.FloatField(null=True, default=None)
    type = models.CharField(max_length=500, null=False, blank=False)
    def __str__(self):
        return self.title

