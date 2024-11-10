from rest_framework import serializers
from .models import Course, Module, Content
from django.conf import settings


class ContentSerializer(serializers.ModelSerializer):
    # Adds a new field for module type
    module_type = serializers.SerializerMethodField()
    # Adds a new field for the media internal path
    media_internal_path = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = '__all__'

    def get_module_type(self, obj):
        return obj.module.type  # Accesses the type field from the related module

    def get_media_internal_path(self, obj):
        # Return the full URL for the media file
        request = self.context.get('request')
        return request.build_absolute_uri(settings.MEDIA_URL + obj.internal_path)



class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    # Nested ModuleSerializer
    modules = ModuleSerializer(many=True)

    class Meta:
        model = Course
        fields = '__all__'