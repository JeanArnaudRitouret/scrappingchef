from rest_framework import serializers
from .models import Path, Training, Step

class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = ['id', 'title', 'type', 'is_validated', 'is_blocked']

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