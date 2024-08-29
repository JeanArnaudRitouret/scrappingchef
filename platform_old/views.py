from django.http import HttpResponse
from django.shortcuts import render
from dotenv import load_dotenv
from .models import Course, Module, Content
from .connect import get_adc_courses, get_adc_modules, get_adc_contents, get_adc_sub_modules
from django.template import loader

load_dotenv()


def get_courses(request=None):
    courses = get_adc_courses()
    context = {"courses": courses}
    return render(request, "adc/courses.html", context)


def list_courses(request=None):
    courses = Course.objects.all()
    context = {"courses": courses}
    return render(request, "adc/courses.html", context)


def get_modules(request=None):
    modules = get_adc_modules(external_course_ids=[])
    context = {"modules": modules}
    return render(request, "adc/modules.html", context)

def get_module_with_id(request=None, external_course_id:int = 0):
    modules = get_adc_modules(external_course_ids=[external_course_id])
    context = {"modules": modules}
    return render(request, "adc/modules.html", context)


def list_modules(request=None, external_course_id:int | None = None):
    if external_course_id:
        modules = Module.objects.filter(
            course_id=external_course_id
        )
    else:
        modules = Module.objects.all()
    context = {"modules": modules}
    return render(request, "adc/modules.html", context)


def get_contents(request=None):
    contents = get_adc_contents(external_course_id=[])
    context = {"contents": contents}
    return render(request, "adc/contents.html", context)


def get_missing_contents(request=None):
    modules = Module.objects.prefetch_related(
        'contents'
    )
    module_ids_without_content = [m.external_id for m in modules if len(m.contents.all())==0]
    print(f"Module Ids with missing content \n{module_ids_without_content}")
    contents = get_adc_contents(external_module_ids=module_ids_without_content)
    context = {"contents": contents}
    return render(request, "adc/contents.html", context)


def get_content_with_course_id(request=None, external_course_id: int = 0):
    contents = get_adc_contents(external_course_id=external_course_id)
    context = {"contents": contents}
    return render(request, "adc/contents.html", context)


def get_content_with_module_id(request=None, module_id: str = ''):
    contents = get_adc_contents(external_module_id=[int(module_id)])
    context = {"contents": contents}
    return render(request, "adc/contents.html", context)


def list_contents(request=None,external_module_id: int | None = None):
    if external_module_id:
        contents = Content.objects.filter(
            module_id=external_module_id
        )
    else:
        contents = Content.objects.all()
    context = {"contents": contents}
    return render(request, "adc/contents.html", context)


def get_sub_modules(request=None, sub_modules_code:str = 'aller_plus_loin'):
    modules = get_adc_sub_modules(sub_modules_code=sub_modules_code)
    context = {"modules": modules}
    return render(request, "adc/modules.html", context)

