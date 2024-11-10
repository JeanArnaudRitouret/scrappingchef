import os
import re
import glob
import shutil
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import requests
from dotenv import load_dotenv
import requests
import pdb


from .enums import ModuleTypes, QuestionTypes
from .models import Course, Module, Content, Quiz, Question, Answer
from .utils import loop_until_get,check_if_folder_exists, loop_until_pass

load_dotenv()

class SeleniumScrapper():

    driver = None
    cookies = None
    internal_path_downloaded_contents=f"{os.environ['PATH_DOWNLOADED_CONTENTS']}/platform_old/"
    save_courses=True
    save_modules=True
    save_contents=True
    loop_limit=10000
    video_download_quality='360p'
    audio_download_code='Audio'


    def __init__(self, extension_vimeo_video_downloader=False):
        options = Options()
        if extension_vimeo_video_downloader:
            options.add_extension(f"{os.environ['PATH_VIDEO_DOWNLOADER']}")
        options.add_argument('--disable-search-engine-choice-screen')
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(
            service=service,
            options=options
        )
        if extension_vimeo_video_downloader:
            time.sleep(5)
            self.driver.switch_to.window(self.driver.window_handles[0])


    def logging(
            self,
            close_pop_up=False
    ):
        self.driver.get(os.environ['URL_LOGIN_ADC'])
        username=os.environ['USERNAME_ADC']
        password=os.environ['PASSWORD_ADC']

        # log in to the formation platform
        username_input = self.driver.find_element(by = 'id', value = "username")
        username_input.send_keys(username)

        password_input = self.driver.find_element(by = 'id', value = "password")
        password_input.send_keys(password)

        ## close the pop up window
        if close_pop_up:
            close_button = loop_until_get(
                get_function=self.get_close_button,
                loop_limit=self.loop_limit,
                error_if_limit_reached=True
            )
            close_button.click()

        login_button = self.driver.find_element(by = 'id', value = "loginbtn")
        login_button.click()

        pass


    def get_close_button(self):
        return self.driver.find_element(by = 'class name', value = 'eupopup-closebutton')

    def get_cookies(self):
        for entry in self.driver.get_cookies():
            if entry['name'] == 'MoodleSession':
                self.cookies = dict({entry['name']:entry['value']})
                pass
        pass


    def expand_parcours_formation(self):
        # expand/de-collapse the block "Mon parcours formation"
        try:
            access_formation_button = self.driver.find_element(
                by = 'class name',
                value = 'lpd-lp-content-header.collapsed.col-12.col-sm-12.col-md-12.col-lg-12.collapsedlpd'
                )
            access_formation_button.click()
        except:
            access_formation_button_2 = self.driver.find_element(
                by = 'class name',
                value = 'lpd-lp-content-header.collapsed.collapsedlpd.col-12.col-sm-12.col-md-12.col-lg-12'
            )
            access_formation_button_2.click()

        pass


    def get_courses(self, save_courses=True):
        courses = []
        self.save_courses=save_courses

        for i in range(1,7): # why the fuck is it hardcoded??
            courses_to_add = self.get_courses_by_page(page_num=i)
            courses += courses_to_add

        if self.save_courses:
            Course.objects.bulk_create(
                objs=courses,
                update_conflicts=True,
                update_fields=[field.__dict__.get('name') for field in Course._meta.get_fields() if field.__dict__.get('primary_key') is False],
                unique_fields=[field.__dict__.get('name') for field in Course._meta.get_fields() if field.__dict__.get('primary_key')]
            )

        return courses


    def get_courses_by_page(self, page_num: int):
        courses = []
        print(f"page num is {page_num}")
        if page_num == 1:
            courses_to_add = loop_until_get(
                get_function=self.get_course_blocks,
                loop_limit=self.loop_limit,
                error_if_limit_reached=True
            )
            print(f"courses_to_add is")
            print(f"{courses_to_add}")
            courses += courses_to_add
        else:
            # first we have to access the right page
            pages_xpath_value = '/html/body/div[1]/div[2]/div/div[2]/div/section/aside/aside[1]/div/div/div[1]/div[2]/div/div[2]/div/div[3]/a'
            pages_and_texts = loop_until_get(
                get_function=self.get_pages_and_texts,
                loop_limit=self.loop_limit,
                error_if_limit_reached=True,
                pages_xpath_value=pages_xpath_value
            )
            # pages_and_texts = self.get_pages_and_texts(pages_xpath_value=pages_xpath_value)
            for text, page in pages_and_texts:
                if text == str(page_num):
                    print(f"page found is {text}")
                    # scrolling down the page to access the page number
                    self.scroll_down_the_page()
                    page.click()
                    courses_to_add = loop_until_get(
                        get_function=self.get_course_blocks,
                        loop_limit=self.loop_limit,
                        error_if_limit_reached=True
                    )
                    print(f"courses_to_add is")
                    print(f"{courses_to_add}")
                    courses += courses_to_add

        return courses


    def scroll_down_the_page(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")


    def get_course_blocks(self):
        courses = []
        # looping through each possible course block
        for i in range(1,100):
            # full xpath for each course block
            module_xpath_value = f'''/html/body/div[1]/div[2]/div/div[2]/div/section/aside/aside[1]/div/div/div[1]/div[2]/div/div[2]/div/div[2]/div[{i}]/div[2]/div[1]/a'''
            elements = self.driver.find_elements(by='xpath', value=module_xpath_value)
            if len(elements)>0:
                course = Course()
                course.title = elements[0].text
                course.link = elements[0].get_attribute('href')
                course.get_course_type()
                course.get_external_id()
                course.get_id()
                courses += [course]
            else:
                break
        return courses

    def get_pages_and_texts(self,pages_xpath_value=None):
        pages_and_texts=[]
        try:
            pages = self.driver.find_elements(by='xpath', value=pages_xpath_value)
            pages_and_texts = [(page.text, page) for page in pages]
        except:
            pass
        return pages_and_texts


    def get_modules(self, external_course_id=None, save_modules=True):
        self.save_modules = save_modules
        url_course = f"{os.environ['URL_ADC_COURSE']}{external_course_id}"
        html_course = self.get_html_page(url=url_course,cookies=self.cookies)
        html_modules = html_course.find_all('li',id=re.compile("^module-"))
        modules = self.create_modules(html_modules=html_modules, external_course_id=external_course_id)
        if self.save_modules:
            #finding out if there are duplicated modules and why
            sorted_modules = sorted( [module.external_id for module in modules])
            duplicated_modules = [module for i,module in enumerate(sorted_modules[1:]) if sorted_modules[i]==module]
            if duplicated_modules:
                breakpoint()

            Module.objects.bulk_create(
                objs=modules,
                update_conflicts=True,
                update_fields=[field.__dict__.get('name') for field in Module._meta.get_fields() if field.__dict__.get('primary_key') is False],
                unique_fields=[field.__dict__.get('name') for field in Module._meta.get_fields() if field.__dict__.get('primary_key')]
            )

        return modules


    def get_html_page(self, url=None, cookies=None):
        req = requests.get(url=url,cookies=cookies)
        return BeautifulSoup(req.text, 'html.parser')


    def create_modules(self, html_modules=None, external_course_id=None):
        modules = []
        for i, html_module in enumerate(html_modules):
            module = Module()
            module.title = html_module.text.replace(html_module.span.span.text, '') if html_module.span.span else html_module.text
            if module.title in (
                'Annonces',
                'Announcements',
                'Annales 2014 - Les Thermes',
                'Votre avis sur la correction de votre exercice pratique',
                'Proposition d\'ordonnancement de travail ',
                'Proposition d\'ordonnancement de travail',
                'Attestation de fin de formation',
                'PSE - Annales 2016',
                'Test PSE 02',
                'PSE - Annales 2017',
                'Test PSE 03',
                'PSE - Annales 2018',
                'Test PSE 04',
                'PSE - Annales 2014',
                'Quelques exemples d\'annales et leurs corrigés',
                'PSE - Annale 2018 - Marc métallier',
                'PSE - Annale 2018 - Marc métallier - CORRIGE',
                'PSE - Annale 2018 - Mathieu cariste',
                'PSE - Annale 2018 - Mathieu cariste - CORRIGE',
                'PSE - Annale 2017 - Adam menuisier',
                'PSE - Annale 2017 - Adam menuisier - CORRIGE'
                ):
                continue
            module.type_extracted = html_module.span.span.text.strip() if html_module.span.span else 'Autre'
            module.type = module.get_module_type()
            module.link = html_module.select('a')[0].get('href') if len(html_module.select('a')) > 0 else None
            module.get_is_completed(html_module)
            module.html_module_index = i

            # print(f"module title is: {module.title}")
            # print(f"module link is: {module.link}")

            # breakpoint()
            # If module is a test not completed, we need to validate to advance
            # if module.type == ModuleTypes.TEST.value and not module.is_completed:
            #     self.driver.get(module.link)
            #     # Get the button t0 go to the test
            #     buttons = self.driver.find_elements(by='tag name', value='button')
            #     test_button = [button for button in buttons if button.text in ('Faire le test','Continuer la dernière tentative')][0]
            #     test_button.click()

            #     # Get the html of the test's page
            #     test_url = self.driver.current_url
            #     request_test = requests.get(test_url, cookies=self.cookies)
            #     html_test = BeautifulSoup(request_test.text, 'html.parser')

            #     # create content if it doesn't exist
            #     content = Content()
            #     content.title = module.title
            #     content.type = 'quiz' # to be improved
            #     # placeholder for internal_path leading to the html page of the quiz?

            #     # create Quiz
            #     quiz = Quiz()
            #     quiz.content = content
            #     quiz.title = module.title
            #     quiz.html_quiz = html_test

            #     # create questions and answers
            #     questions = self.create_questions(quiz=quiz)
            #     answers = self.create_answers(questions=questions)

            #     # click right answers
            #     self.click_right_answers(answers)

            #     breakpoint()

            #     # click button to terminate test
            #     self.complete_test()

            #     breakpoint()

            module.course = Course.objects.get(external_id=external_course_id)
            modules += [module]

        modules_with_link = self.add_modules_link_and_id(modules)

        return modules_with_link


    def create_questions(self, quiz):
        questions = []
        html_question_blocks = quiz.html_quiz.find_all('div',class_="formulation clearfix")
        for html_question_block in html_question_blocks:
            # Find out the type of question
            if html_question_block.select('select[class*="m-l-1"]'):
                questions += self.create_select_questions(quiz=quiz, html_question_block=html_question_block)
            elif html_question_block.find("input", type="radio"):
                questions += self.create_radio_questions(quiz=quiz, html_question_block=html_question_block)
            elif html_question_block.find("input", type="checkbox"):
                questions += self.create_checkbox_questions(quiz=quiz, html_question_block=html_question_block)
            elif html_question_block.select('select[class*="place"]'):
                questions += self.create_control_group_questions(quiz=quiz, html_question_block=html_question_block)
            else:
                raise Exception(f"Error: Question type unknown")
        return questions


    def create_select_questions(self, quiz=None, html_question_block=None):
        questions=[]
        question_headline_text = html_question_block.find_all('span')[0].text
        html_questions = html_question_block.find_all('tr')
        for html_question in html_questions:
            question = Question()
            question.quiz = quiz
            question_footer_text = html_question.find_all('td', class_='text')[0].text
            question.text = question_headline_text + ' ' + question_footer_text
            question.html_question = html_question
            question.type = QuestionTypes.SELECT.value
            questions += [question]
        return questions


    def create_radio_questions(self, quiz=None, html_question_block=None):
        question_text = html_question_block.find('span').text
        question = Question()
        question.quiz = quiz
        question.text = question_text
        question.html_question = html_question_block
        question.type = QuestionTypes.RADIO.value
        return [question]


    def create_checkbox_questions(self, quiz=None, html_question_block=None):
        question_text = html_question_block.find('span').text
        question = Question()
        question.quiz = quiz
        question.text = question_text
        question.html_question = html_question_block
        question.type = QuestionTypes.CHECKBOX.value
        return [question]


    def create_control_group_questions(self, quiz=None, html_question_block=None):
        question_text = html_question_block.find_all("p")[0].text
        question = Question()
        question.quiz = quiz
        question.text = question_text
        question.html_question = html_question_block
        question.type = QuestionTypes.CONTROL_GROUP.value
        return [question]


    def create_answers(self, questions=None):
        answers = []
        for question in questions:
            if question.type == QuestionTypes.SELECT.value:
                answers += self.create_select_answers(question=question)
            elif question.type == QuestionTypes.RADIO.value:
                answers += self.create_radio_answers(question=question)
            elif question.type == QuestionTypes.CHECKBOX.value:
                answers += self.create_checkbox_answers(question=question)
            elif question.type == QuestionTypes.CONTROL_GROUP.value:
                answers += self.create_control_group_answers(question=question)
            else:
                raise Exception(f"Error: Question type unknown")
        return answers


    def create_select_answers(self, question=None):
        answers = []
        html_answers = [option for option in question.html_question.find_all('option') if option['value'] != "0"]
        for html_answer in html_answers:
            answer = Answer()
            answer.question = question
            answer.text = html_answer.text
            answer.is_right_answer = answer.get_is_right_answer()
            answer.html_answer = html_answer
            answers += [answer]
        return answers


    def create_radio_answers(self, question=None):
        answers = []
        html_answers = question.html_question.find("div", class_="answer").find_all("div")
        for html_answer in html_answers:
            answer = Answer()
            answer.question = question
            answer.text = html_answer.text
            answer.is_right_answer = answer.get_is_right_answer()
            answer.html_answer = html_answer
            answers += [answer]
        return answers


    def create_checkbox_answers(self, question=None):
        answers = []
        html_answers = question.html_question.find("div", class_="answer").find_all("div")
        for html_answer in html_answers:
            answer = Answer()
            answer.question = question
            answer.text = html_answer.text
            answer.is_right_answer = answer.get_is_right_answer()
            answer.html_answer = html_answer
            answers += [answer]
        return answers


    def create_control_group_answers(self, question=None):
        answers = []
        html_control_groups = question.html_question.select('select[class*="place"]')
        for control_group_rank, html_control_group in enumerate(html_control_groups):
            html_answers = [option for option in html_control_group.find_all('option') if option['value'] != ""]
            for html_answer in html_answers:
                answer = Answer()
                answer.question = question
                answer.text = html_answer.text
                answer.control_group_rank = control_group_rank
                answer.is_right_answer = answer.get_is_right_answer()
                answer.html_answer = html_answer
                answer.html_control_group = html_control_group
                answers += [answer]
        return answers


    def click_right_answers(self, answers):
        for answer in answers:
            if answer.is_right_answer:
                if answer.question.type == QuestionTypes.SELECT.value:
                    self.driver.find_element(
                        by="id", value=answer.question.html_question.find_all('select')[0].get("id")
                    ).find_element(
                        by='css selector',
                        value=f'option[value="{answer.html_answer.get("value")}"]'
                    ).click()
                if answer.question.type == QuestionTypes.RADIO.value:
                    self.driver.find_element(by="id", value=answer.html_answer.find("input").get("id")).click()
                if answer.question.type == QuestionTypes.CHECKBOX.value:
                    checkbox = self.driver.find_element(by="id", value=answer.html_answer.find_all("input")[1].get("id"))
                    if not checkbox.is_selected():
                        checkbox.click()
                if answer.question.type == QuestionTypes.CONTROL_GROUP.value:
                    self.driver.find_element(
                        by="id", value=answer.html_control_group.get("id")
                    ).find_element(
                        by='css selector',
                        value=f'option[value="{answer.html_answer.get("value")}"]'
                    ).click()


    def complete_test(self):
        # Go to summary page
        test_url = self.driver.current_url
        summary_url = test_url.replace('attempt','summary', 1)
        self.driver.get(summary_url)

        # Get summary page completion button
        summary_buttons = loop_until_get(
            get_function=self.get_summary_buttons,
            loop_limit=self.loop_limit,
            error_if_limit_reached=True
        )
        completion_button = [button for button in summary_buttons if button.text == 'Tout envoyer et terminer'][0]
        completion_button.click()

        # Click popup completion button
        loop_until_get(
            get_function=self.click_popup_button,
            loop_limit=self.loop_limit,
            error_if_limit_reached=True
        )


    def get_summary_buttons(self):
        try:
            summary_buttons = self.driver.find_elements(by="css selector", value="button[type='submit']")
            return summary_buttons
        except:
            pass

    def click_popup_button(self):
        try:
            popup_completion_button = self.driver.find_element(by='css selector', value='input[value="Tout envoyer et terminer"]')
            popup_completion_button.click()
        except:
            pass


    def click_completion_button(self):
        self.driver.find_element(
            by='css selector',
            value=f'input[value="Terminer le test…"]'
        ).click()


    def add_modules_link_and_id(self, modules=None):
        for index, module in enumerate(modules):
            if not module.link:
                previous_index = index - 1
                previous_link = modules[previous_index].link
                request_previous_module = requests.get(previous_link, cookies=self.cookies)
                html_previous_modules = BeautifulSoup(request_previous_module.text, 'html.parser')
                previous_modules = html_previous_modules.find_all('li',id=re.compile("^module-"))
                if not previous_modules[module.html_module_index].select('a'):
                    # this usually means we need to do some manual validation and relaunch the scrapping
                    breakpoint()
                module.link = previous_modules[module.html_module_index].select('a')[0].get('href')

            module.get_external_id()
            module.get_id()

        return modules


    def get_contents(
            self,
            external_course_id:int =None,
            external_module_ids:list[int]=[],
            save_contents=True
        ) -> list[Content]:
        """
        This function queries the modules with content to be scrapped.
        The list of modules is eitheer all the modules related to the external_course_id or the list of external_module_ids.
        Then for each module we check if the contents already exists, and scraps it otherwise.

        Args:
            external_course_id (int, optional): _description_. Defaults to None.
            external_module_ids (list[int], optional): _description_. Defaults to [].
            save_contents (bool, optional): _description_. Defaults to True.

        Raises:
            Exception: _description_

        Returns:
            list[Content]: _description_
        """
        contents=[]
        existing_content = Content.objects.all()
        self.save_contents = save_contents

        # If a external_course_id is informed, we are querying all the modules related to the course
        if external_course_id:
            modules = Module.objects.filter(course__external_id=external_course_id)
        # If a list of external_module_id is informed, we are querying the modules
        elif external_module_ids:
            modules = Module.objects.filter(external_id__in=external_module_ids)
        else:
            raise Exception(f"Error: Either external_course_id or external_module_id requested to get contents")


        for module in modules:
            # if this module has already a related content, we don't need to create the content again
            if module.id in [c.module_id for c in existing_content]:
                content = None
            else:
                content = self.get_content(module=module)
            if content:
                contents += [content]

            # Content.objects.bulk_create(contents)

        return contents


    def get_content(self, module=None):
        if module.type == ModuleTypes.FICHIER.value:
            content = self.get_content_fichier(module=module)
        elif module.type == ModuleTypes.VIDEO.value:
            content = self.get_content_video(module=module)
        elif module.type == ModuleTypes.PAGE.value:
            content = self.get_content_page(module=module)
        else:
            content = None
        if content and self.save_contents:
            Content.objects.bulk_create(
                objs=[content],
                update_conflicts=True,
                update_fields=[field.__dict__.get('name') for field in Content._meta.get_fields() if field.__dict__.get('primary_key') is False],
                unique_fields=[field.__dict__.get('name') for field in Content._meta.get_fields() if field.__dict__.get('primary_key')]
            )
        return content


    def get_content_fichier(self, module=None):
        fichier_url = module.link
        request_fichier = requests.get(fichier_url,cookies=self.cookies)
        html_fichier = BeautifulSoup(request_fichier.text, 'html.parser')
        pdf_url = self.get_pdf_url(html_fichier=html_fichier)

        if not pdf_url:
            return None

        request_pdf = requests.get(pdf_url, cookies=self.cookies)
        if request_pdf.status_code == 200:
            path_download_content = f"{self.internal_path_downloaded_contents}/{module.course_id}/{module.external_id}"
            check_if_folder_exists(folder_path=path_download_content, create_folder=True)
            path_download_content_fichier = f"{path_download_content}/{module.title.replace('/','-')}.pdf"
            with open(f"{path_download_content_fichier}", "wb") as f:
                f.write(request_pdf.content)

            content = Content()
            content.module = module
            content.title = f"{module.title.replace('/','-')}.pdf"
            content.get_type()
            content.internal_path = path_download_content_fichier
            return content
        else:
            raise Exception(f"Error: Request failed. Status code: {request_pdf.status_code}. Content from module not saved.")


    def get_pdf_url(self, html_fichier):
        if html_fichier.find_all('div', class_='resourcecontent resourcepdf'):
            return html_fichier.find_all('div', class_='resourcecontent resourcepdf')[0].select('a')[0].get('href')
        return None


    def get_content_video(self, module=None):
        module_video_url = module.link
        request_module_video = requests.get(module_video_url, cookies=self.cookies)
        html_module_video = BeautifulSoup(request_module_video.text, 'html.parser')
        vimeo_video_url = html_module_video.find_all('iframe', id='plms-video')[0]['src']
        if vimeo_video_url == 'https://player.vimeo.com/video/538582747?api=1&player_id=plms-video':
            breakpoint()
        self.driver.get(vimeo_video_url)

        video_name, copied_video_path = self.download_video(module)
        audio_name, copied_audio_path = self.download_audio(module)

        content = Content()
        content.module = module
        content.title = f"{video_name}"
        content.get_type()
        content.internal_path = copied_video_path
        return content


    def download_video(self, module):

        # loop until 1/ we get the download button and 2/ it is clickable (and not stale for instance)

        loop_until_pass(
            pass_function=self.get_and_click_download_button,
            loop_limit=self.loop_limit,
            error_if_limit_reached=True,
            download_type='video'
        )

        # let it sleep to make sure we have downoaded the video
        time.sleep(5)

        # move video to right content folder (video can be without sound)
        downloaded_video_path = max(glob.glob('/Users/jeanarnaudritouret/Downloads/*.mp4'), key=os.path.getctime)
        video_name = re.search('(/Users/jeanarnaudritouret/Downloads/)(.*.mp4)', downloaded_video_path).group(2)
        path_download_content = f"{self.internal_path_downloaded_contents}/{module.course_id}/{module.external_id}"
        check_if_folder_exists(folder_path=path_download_content, create_folder=True)
        copied_video_path = f"{path_download_content}/{video_name}"
        shutil.copy(downloaded_video_path, copied_video_path)
        print(f"video downloaded for module {module.id}")
        print(f"video name is {video_name}")

        return  video_name, copied_video_path


    def get_and_click_download_button(self, download_type:str = ''):
        # get the download button
        download_button = loop_until_get(
            get_function=self.get_download_button,
            loop_limit=self.loop_limit,
            error_if_limit_reached=True,
            download_type=download_type
        )
        # download the video
        download_button.click()
        pass


    def download_audio(self, module):
        # download and move video to right content folder (video can be without sound)
        download_button=self.get_download_button(download_type='audio')
        if not download_button:
            return None, None
        try:
            download_button.click()
        except StaleElementReferenceException as e:
            print("StaleElementReferenceException caught!")
            pdb.set_trace()

        time.sleep(5)
        downloaded_audio_path = max(glob.glob('/Users/jeanarnaudritouret/Downloads/*.mp4'), key=os.path.getctime)
        audio_name = re.search('(/Users/jeanarnaudritouret/Downloads/)(.*.mp4)', downloaded_audio_path).group(2)
        path_download_content = f"{self.internal_path_downloaded_contents}/{module.course_id}/{module.external_id}"
        check_if_folder_exists(folder_path=path_download_content, create_folder=True)
        copied_audio_path = f"{path_download_content}/{audio_name}"
        shutil.copy(downloaded_audio_path, copied_audio_path)
        print(f"audio downloaded for module {module.id}")
        print(f"audio namenane is {audio_name}")

        return  audio_name, copied_audio_path


    def get_download_button(self, download_type:str = ''):
        buttons_dict = loop_until_get(
            get_function=self.get_buttons_dict,
            loop_limit=self.loop_limit,
            error_if_limit_reached=True
        )
        if download_type == 'video' and self.video_download_quality in buttons_dict.keys():
            return buttons_dict[self.video_download_quality]
        if download_type == 'audio' and self.audio_download_code in buttons_dict.keys():
            return buttons_dict[self.audio_download_code]
        return None


    def get_buttons_dict(self):
        buttons_dict = {}
        buttons = self.driver.find_elements(by = 'tag name', value = "button")
        for button in buttons:
            try:
                buttons_dict[button.text] = button
            except StaleElementReferenceException:
                continue
        return buttons_dict


    def get_content_page(self, module=None):
        module_page_url = module.link
        request_page = requests.get(module_page_url,cookies=self.cookies)
        html_page = BeautifulSoup(request_page.text, 'html.parser')

        path_download_content = f"{self.internal_path_downloaded_contents}/{module.course_id}/{module.external_id}"
        check_if_folder_exists(folder_path=path_download_content, create_folder=True)

        path_download_content_page = f"{path_download_content}/{module.title.replace('/','-')}.html"
        with open(f"{path_download_content_page}", "w") as f:
            f.write(str(html_page.find_all('div', role='main')[0]))

        content = Content()
        content.module = module
        content.title = f"{module.title.replace('/','-')}.html"
        content.get_type()
        content.internal_path = path_download_content_page
        return content
