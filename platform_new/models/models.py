from django.db import models


class BaseModel(models.Model):
    id = models.CharField(primary_key=True, max_length=500)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Path(BaseModel):
    platform_id = models.CharField(max_length=500, null=False, blank=False, unique=True)
    title = models.CharField(max_length=500, null=False, blank=False)
    progression = models.FloatField(null=False, blank=False)
    score = models.FloatField(null=False, blank=False)

    def __str__(self) -> str:
        return str(self.title)


class Training(BaseModel):
    platform_id = models.CharField(max_length=500, null=False, blank=False, unique=True)
    path = models.ForeignKey(Path, related_name='trainings', on_delete=models.CASCADE, null=False, blank=False)
    title = models.CharField(max_length=500, null=False, blank=False)
    progression = models.FloatField(null=False)
    score = models.FloatField(null=False)
    type = models.CharField(max_length=500, null=False, blank=False)

    def __str__(self) -> str:
        return str(self.title)


class Step(BaseModel):
    platform_id = models.IntegerField(null=False, blank=False, unique=True)
    training = models.ForeignKey(Training, related_name='steps', on_delete=models.CASCADE, null=False, blank=False)
    title = models.CharField(max_length=500, null=False, blank=False)
    type = models.CharField(max_length=500, null=False, blank=False)
    is_validated = models.BooleanField(default=False, null=False, blank=False)  # type: ignore
    is_blocked = models.BooleanField(default=False, null=False, blank=False)  # type: ignore

    def __str__(self) -> str:
        return str(self.title)


class Content(BaseModel):
    step = models.ForeignKey(Step, related_name='contents', on_delete=models.CASCADE, null=False, blank=False)
    filename = models.CharField(max_length=500, null=False, blank=False)
    type = models.CharField(max_length=500, null=False, blank=False)

    def __str__(self) -> str:
        return str(self.filename)
