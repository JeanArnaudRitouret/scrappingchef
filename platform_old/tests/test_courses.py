from django.test import TestCase
from django.db.models import Count
from ..models import Course

class CourseTest(TestCase):


    def test_courses_exist(self) -> None:
        """
        Test to ensure that at least 1 module has been created.
        """
        # get list of courses
        courses = Course.objects.all()

        # assert if this list is not empty
        assert len(courses) > 0, f"there are {len(courses)} courses"


    def test_courses_have_content(self) -> None:
        """
        Test to ensure that each course has at least one related module.
        """
        # get list of courses without any related module
        courses_without_modules = Course.objects.annotate(num_modules=Count('modules')).filter(num_modules=0)

        # assert if this list is empty
        assert len(courses_without_modules) == 0, f"there are {len(courses_without_modules)} courses without modules"