import os
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv

from scrappingchef.utils import loop_until_get

load_dotenv()

class SeleniumScrapper():

    driver = None
    cookies = None
    internal_path_downloaded_contents=f"{os.environ['PATH_DOWNLOADED_CONTENTS']}/platform_new/"
    save_courses=True
    save_modules=True
    save_contents=True
    loop_limit=10000
    video_download_quality='360p'
    audio_download_code='Audio'


    def __init__(self, extension_vimeo_video_downloader=False):
        # Set the options for the Chrome browser, useful to customize the scrapping behaviour
        options = Options()
        # Run in headless mode, useful to avoid opening a browser window
        # Add the extension to download Vimeo videos if necessary
        if extension_vimeo_video_downloader:
            options.add_extension(f"{os.environ['PATH_VIDEO_DOWNLOADER']}")

        # Add options for cloud environment
        if os.getenv('GAE_ENV', '').startswith('standard') or os.getenv('CLOUD_RUN_JOB', ''):
            options.add_argument('--headless')
            options.add_argument('--no-sandbox') # Disable the sandbox, required for cloud environment
            options.add_argument('--disable-dev-shm-usage') # Handle memory issues on cloud environment
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')

        # Set up the driver with options and the link to the ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(
            service=service,
            options=options
        )

        # Switch to the first window instead of the vimdeo extension window if the extension has been added
        if extension_vimeo_video_downloader:
            time.sleep(5)
            self.driver.switch_to.window(self.driver.window_handles[0])

        self.logging()
        self.get_cookies()


    def logging(self):
        # Go to the login page
        self.driver.get(os.environ['URL_LOGIN_NEW_PLATFORM'])

        # Input the username and password
        username_input = self.driver.find_element(by = 'id', value = "username")
        password_input = self.driver.find_element(by = 'id', value = "password")
        username_input.send_keys(os.environ['USERNAME_ADC'])
        password_input.send_keys(os.environ['PASSWORD_ADC'])

        # Click on the login button
        login_button = self.driver.find_element(by = 'id', value = "js-login-form-submit")
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