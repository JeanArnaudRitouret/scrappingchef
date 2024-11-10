import os
from django.test import TestCase
from django.db.models import Count
from ..models import Content

class ContentTest(TestCase):


    def test_contents_exist(self) -> None:
        """
        Test to ensure that at least 1 content has been created.
        """
        # get list of contents
        contents = Content.objects.all()

        # assert if this list is empty
        assert len(contents) > 0, f"there are {len(contents)} contents"


    def test_contents_have_downloaded_objects(self) -> None:
        """
        Test to ensure that each contents has at least one downloaded object.
        """
        # get list of contents without any related download objects
        contents = Content.objects.all()
        internal_path_downloaded_contents=f"{os.environ['PATH_DOWNLOADED_CONTENTS']}/platform_old/"

        for each content in contents:
            # get path of downloaded object(s) for this content
            download_object_internal_path = content.internal_path

            # assert if this list is empty
            assert len(downloaded_objects) > 0, f"there are {len(downloaded_objects)} downloaded objects for content {content}"

        # assert if this list is empty
        assert len(contents_without_downloaded_objects) == 0, f"there are {len(contents_without_downloaded_objects)} contents without downloaded objects"