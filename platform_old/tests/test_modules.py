from django.test import TestCase
from django.db.models import Count
from ..models import Module

class ModuleTest(TestCase):


    def test_modules_exist(self) -> None:
        """
        Test to ensure that at least 1 module has been created.
        """
        # get list of modules without any related content
        modules = Module.objects.all()

        # assert if this list is empty
        print(f"there are {len(modules)} modules")
        assert len(modules) > 0, f"there are {len(modules)} modules"


    def test_modules_have_content(self) -> None:
        """
        Test to ensure that each module has at least one related content.
        """
        # get list of modules without any related content
        modules_without_contents = Module.objects.annotate(num_contents=Count('contents')).filter(num_contents=0)

        # assert if this list is empty
        assert len(modules_without_contents) == 0, f"there are {len(modules_without_contents)} modules without content"