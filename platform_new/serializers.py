from rest_framework import serializers
from .models.models import Path, Training, Step, Content


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ['id', 'filename', 'type']


class StepSerializer(serializers.ModelSerializer):
    contents = ContentSerializer(many=True, read_only=True)

    class Meta:
        model = Step
        fields = ['id', 'title', 'type', 'is_validated', 'is_blocked', 'contents']


class TrainingSerializer(serializers.ModelSerializer):
    steps = StepSerializer(many=True, read_only=True)

    class Meta:
        model = Training
        fields = ['id', 'title', 'type', 'progression', 'steps']


class PathSerializer(serializers.ModelSerializer):
    trainings = TrainingSerializer(many=True, read_only=True)

    class Meta:
        model = Path
        fields = ['id', 'title', 'progression', 'score', 'trainings']