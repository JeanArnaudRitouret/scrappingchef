from typing import Any
from django.http import HttpResponse
from django.shortcuts import render
from dotenv import load_dotenv
from .models import Course, Module, Content
from .connect import get_platform_courses, get_platform_modules, get_platform_contents, get_platform_sub_modules
from django.template import loader

load_dotenv()


def get_courses(request: Any | None = None):
    courses = get_platform_courses()
    context = {"courses": courses}
    return render(request, "platform_old/courses.html", context)


def list_courses(request: Any | None = None):
    courses = Course.objects.all()
    context = {"courses": courses}
    return render(request, "platform_old/courses.html", context)


def get_modules(request: Any | None = None) -> HttpResponse:
    """
    Download the modules by looping through all the courses already downloaded.

    Args:
        request (Any | None, optional). Defaults to None.

    Returns:
        HttpResponse: object with a rendered text which is a combination of a template with a context dictionary
    """
    # Since external_course_ids is empty, all the courses in the database are looped
    modules = get_platform_modules(external_course_ids=[])
    context = {"modules": modules}
    return render(request, "platform_old/modules.html", context)

def get_module_with_id(request: Any | None = None, external_course_id:int = 0) -> HttpResponse:
    modules = get_platform_modules(external_course_ids=[external_course_id])
    context = {"modules": modules}
    return render(request, "platform_old/modules.html", context)


def list_modules(request: Any | None = None, external_course_id:int | None = None) -> HttpResponse:
    """
    List the downloaded modules, for a specific course if a course_id is given or for all modules if no course_id is given.

    Args:
        request (Any | None, optional). Defaults to None.
        external_course_id (int | None, optional) the sepcific course_id to search modules for. Defaults to None.

    Returns:
        HttpResponse: object with a rendered text which is a combination of a template with a context dictionary
    """
    if external_course_id:
        modules = Module.objects.filter(
            course_id=external_course_id
        )
    else:
        modules = Module.objects.all()
    context = {"modules": modules}
    return render(request, "platform_old/modules.html", context)


def get_contents(request=None):
    contents = get_platform_contents(external_course_id=[])
    context = {"contents": contents}
    return render(request, "platform_old/contents.html", context)


def get_missing_contents(request=None):
    modules = Module.objects.prefetch_related(
        'contents'
    )
    module_ids_without_content = [m.external_id for m in modules if len(m.contents.all())==0]
    print(f"Module Ids with missing content \n{module_ids_without_content}")
    contents = get_platform_contents(external_module_ids=module_ids_without_content)
    context = {"contents": contents}
    return render(request, "platform_old/contents.html", context)


def get_content_with_course_id(request=None, external_course_id: int = 0):
    contents = get_platform_contents(external_course_id=external_course_id)
    context = {"contents": contents}
    return render(request, "platform_old/contents.html", context)


def get_content_with_module_id(request=None, module_id: str = ''):
    contents = get_platform_contents(external_module_id=[int(module_id)])
    context = {"contents": contents}
    return render(request, "platform_old/contents.html", context)


def list_contents(request=None,external_module_id: int | None = None):
    if external_module_id:
        contents = Content.objects.filter(
            module_id=external_module_id
        )
    else:
        contents = Content.objects.all()
    context = {"contents": contents}
    return render(request, "platform_old/contents.html", context)


def get_sub_modules(request=None, sub_modules_code:str = 'aller_plus_loin'):
    modules = get_platform_sub_modules(sub_modules_code=sub_modules_code)
    context = {"modules": modules}
    return render(request, "platform_old/modules.html", context)

