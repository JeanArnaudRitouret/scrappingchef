from django.urls import path
from .views import index
from django.conf import settings
from django.conf.urls.static import static
import os

from . import views

app_name = "adc_new"
urlpatterns = [
    path('', index, name='index'),
    path("scrap_paths_and_trainings/", views.scrap_paths_and_trainings, name="scrap_paths_and_trainings"),
    path("list_scrapped_paths/", views.list_scrapped_paths, name="list_scrapped_paths"),
    path("list_scrapped_trainings/", views.list_scrapped_trainings, name="list_scrapped_trainings")
]


# Media files handling
IS_GAE = bool(os.getenv('GAE_APPLICATION', False))
if not IS_GAE:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

