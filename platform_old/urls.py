from django.urls import path
from .views import CourseList, ContentForModule, index
from django.conf import settings
from django.conf.urls.static import static


from . import views

app_name = "adc3"
urlpatterns = [
    path('api/content/<str:moduleID>/', ContentForModule.as_view(), name='content-for-module'),
    path('api/courses/', CourseList.as_view(), name='course_list'),
    path('', index, name='index'),
    path("get_courses/", views.get_courses, name="get_courses"),
    path("list_courses/", views.list_courses, name="list_courses"),
    path("get_modules/", views.get_modules, name="get_modules"),
    path("get_module_with_id/<int:external_course_id>", views.get_module_with_id, name="get_module_with_id"),
    path("list_modules/", views.list_modules, name="list_modules"),
    path("list_modules/<int:external_course_id>", views.list_modules, name="list_modules"),
    path("get_contents/", views.get_contents, name="get_contents"),
    path("get_missing_contents/", views.get_missing_contents, name="get_missing_contents"),
    path("get_content_with_course_id/<int:external_course_id>", views.get_content_with_course_id, name="get_content_with_course_id"),
    path("get_content_with_module_id/<str:module_id>", views.get_content_with_module_id, name="get_content_with_module_id"),
    path("list_contents/", views.list_contents, name="list_contents_default"),
    path("list_contents/<int:external_module_id>", views.list_contents, name="list_contents"),
    path("get_sub_modules/", views.get_sub_modules, name="get_sub_modules"),
]

# Only in development, we serve media files
# TODO: Need a web server to handle static and media files in production (Nginx or Apache)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
