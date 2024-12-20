from django.urls import path
from .views import index, PathsHierarchyView
from django.conf import settings
from django.conf.urls.static import static
import os

from . import views

app_name = "adc_new"
urlpatterns = [
    path('', index, name='index'),
    path("scrap_all_paths_and_trainings/", views.scrap_all_paths_and_trainings, name="scrap_all_paths_and_trainings"),
    path("scrap_steps_for_training/<int:training_id>/", views.scrap_steps_for_training, name="scrap_steps_for_training"),
    path("scrap_all_steps/", views.scrap_all_steps, name="scrap_all_steps"),
    path("list_scrapped_paths/", views.list_scrapped_paths, name="list_scrapped_paths"),
    path("list_scrapped_trainings/", views.list_scrapped_trainings, name="list_scrapped_trainings"),
    path("list_scrapped_steps/", views.list_scrapped_steps, name="list_scrapped_steps"),
    path('api/paths-hierarchy/', PathsHierarchyView.as_view(), name='paths-hierarchy'),
]


# Media files handling
IS_GAE = bool(os.getenv('GAE_APPLICATION', False))
if not IS_GAE:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

