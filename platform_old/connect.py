import os
from dotenv import load_dotenv
from .scrapper import SeleniumScrapper
from .models import Course, Module, Content

load_dotenv()

def get_adc_courses():
    scrapper = SeleniumScrapper()
    scrapper.logging(close_pop_up=True)
    scrapper.get_cookies()
    scrapper.expand_parcours_formation()
    return scrapper.get_courses()


def get_adc_modules(external_course_ids=None):
    modules = []
    scrapper = SeleniumScrapper()
    scrapper.logging(close_pop_up=True)
    scrapper.get_cookies()
    if not external_course_ids:
        external_course_ids = [qs_value['external_id'] for qs_value in Course.objects.values('external_id').distinct()]
    for external_course_id in external_course_ids:
        scrapper.driver.get(f"{os.environ['URL_ADC_COURSE']}{external_course_id}")
        modules += scrapper.get_modules(external_course_id=external_course_id)
    return modules

def get_adc_contents(
        external_course_id:int = 0,
        external_module_ids:list[int] = []
    ):
    """
    This function initiates the Selenium scraper, gets to the course or module where the content(s) is, scrap the related contents locally and returns them.
    By default, if no course or module id is given, all the courses are looped and their contents are scrapped.

    Args:
        external_course_id (int, optional): the course with the related contents to scrap. Defaults to 0.
        external_module_id (list[int], optional): a list of modules with related contents to scrap. Defaults to [].

    Returns:
        list[Content]: list of related contents scrapped
    """
    contents = []
    scrapper = SeleniumScrapper(extension_vimeo_video_downloader=True)
    scrapper.logging(close_pop_up=True)
    scrapper.get_cookies()
    if external_course_id:
        # The scrapper opens the course page, then the content related to each module of the course is downloaded
        scrapper.driver.get(f"{os.environ['URL_ADC_COURSE']}{external_course_id}")
        contents = scrapper.get_contents(external_course_id=external_course_id)
    elif external_module_ids:
        # The scrapper opens the first module page, then the content of the module page is scrapped
        scrapper.driver.get(f"{Module.objects.get(external_id=external_module_ids[0]).link}")
        contents = scrapper.get_contents(external_module_ids=external_module_ids)
    else:
        external_course_ids = [qs_value['external_id'] for qs_value in Course.objects.values('external_id').distinct()]
        for external_course_id in external_course_ids:
            scrapper.driver.get(f"{os.environ['URL_ADC_COURSE']}{external_course_id}")
            contents += scrapper.get_contents(external_course_id=external_course_id)
    return contents


def get_adc_sub_modules(sub_modules_code:str = ''):
    if sub_modules_code == 'aller_plus_loin':
        contents = Content.objects.filter(title__icontains="aller plus loin")
        content = contents[0]
        with open(f"{content.internal_path}", "r") as html_file:
            data = html_file.read()
            breakpoint()



if __name__ == "__main__":
    get_adc_courses()
