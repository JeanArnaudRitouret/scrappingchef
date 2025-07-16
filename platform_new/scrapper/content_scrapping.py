import logging
import os
import time
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import yt_dlp
from platform_new.models.step_type import StepType
from platform_new.scrapper.scrapper import SeleniumScrapper
from platform_new.models.models import Content, Step, Training
from platform_new.scrapper.step_scrapping import get_scrapped_step_objects_for_training_module
from urllib.parse import unquote, urlparse, parse_qs

# TODO: Remove hardcoded urls

# CSS selectors used for step scraping
SELECTORS = {
    'module_item': '.training-view-module-item',
    'title': '.training-view-module-item-title', 
    'state': '.training-view-module-item-state .state-box',
    'icon': '.item-icon-picto i'
}


def get_scrapped_content_objects_for_training_module(scrapper: SeleniumScrapper, training_id: int) -> list[Content]:
    try:
        steps = get_scrapped_step_objects_for_training_module(scrapper=scrapper, training_id=training_id)

        unblock_all_steps(scrapper=scrapper, steps=steps)

        contents = []
        for i, step in enumerate(steps):
            # We have to navigate to each step to get the content
            navigate_to_step_module(scrapper, i)

            if step.type == StepType.TEXT.value:
                content = process_step_text_content(scrapper, step)
                contents.append(content)

            elif step.type == StepType.DOCUMENT.value:
                content = process_step_document_content(scrapper, step)
                contents.append(content)

            elif step.type == StepType.VIDEO.value:
                content = process_step_video_content(scrapper, step)
                contents.append(content)

        return contents

    except Exception as e:
        logging.error(f"Error scraping steps: {str(e)}")
        logging.error(f"Stopped at step index {i} (step_id: {steps[i].id})")
        return []


def process_step_video_content(scrapper: SeleniumScrapper, step: Step) -> Content:
    try:
        iframe_src = get_iframely_src(scrapper.driver)
        video_download_url = get_video_download_url(iframe_src)
        file_name=f"content_{step.id}.mp4"
        file_path = prepare_file_path(file_name=file_name)
        download_video_with_ytdlp(video_download_url, file_path)
    except Exception as e:
        logging.error(f"Error processing video content: {str(e)}")
        download_url = None

    # Create a new Content object for the video
    content = Content(
        id=step.id,
        step=step,
        filename=file_name,
        type="video"
    )

    return content


def download_video_with_ytdlp(video_url: str, output_path: str) -> None:
    """
    Downloads a video using yt-dlp with minimal format options.

    Args:
        video_url (str): URL of the video to download
        output_path (str): Path where the video should be saved

    Raises:
        yt_dlp.utils.DownloadError: If video download fails
    """
    ydl_opts = {
        'outtmpl': output_path
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # First get available formats
            info = ydl.extract_info(video_url, download=False)
            # Then download
            ydl.download([video_url])
        except yt_dlp.utils.DownloadError as e:
            logging.error(f"Failed to download video: {str(e)}")
            raise


def get_video_download_url(iframe_src: str) -> str:
    """
    Extracts the Vimeo video download URL from an iframely src URL.

    Args:
        iframe_src (str): The source URL from the iframely iframe

    Returns:
        str: The Vimeo video download URL
    """
    try:
        # Parse the iframely URL to get the encoded Vimeo URL
        parsed = urlparse(iframe_src)
        query_params = parse_qs(parsed.query)
        # Get and decode the original Vimeo URL
        vimeo_url = unquote(query_params['url'][0])
        video_id = vimeo_url.split('vimeo.com/')[-1]
        return f'https://player.vimeo.com/video/{video_id}'
    except (KeyError, IndexError) as e:
        logging.error(f"Failed to parse video URL: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error getting video URL: {str(e)}")
        raise


def get_iframely_src(driver) -> str:
    """
    Gets the src attribute of the iframely iframe from the page.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        str: The src URL of the iframely iframe

    Raises:
        TimeoutException: If no iframely iframe is found within timeout
    """
    iframe = WebDriverWait(driver, 10).until(
        lambda driver: next(
            (frame for frame in driver.find_elements(By.TAG_NAME, "iframe") 
            if frame.get_attribute('src') and 'iframe.ly' in frame.get_attribute('src')),
            None
        )
    )
    if not iframe:
        raise TimeoutException("No iframe with iframe.ly source found")

    return iframe.get_attribute('src')


def process_step_document_content(scrapper: SeleniumScrapper, step: Step) -> Content:
    content, pdf_url = get_content_and_pdf_url_for_step(scrapper, step)

    if not content or not pdf_url:
        logging.error(f"Failed to get content for step {step.id}: Empty content or HTML")
        return None

    download_pdf(pdf_url, step.id)

    return content


def get_content_and_pdf_url_for_step(scrapper: SeleniumScrapper, step: Step) -> tuple[Content, str]:
    content = Content(
        id=step.id,
        step=step,
        filename=f"content_{step.id}.pdf",
        type="document",
    )
    pdf_url = get_pdf_url(scrapper)

    return content, pdf_url


def download_pdf(pdf_url: str, step_id: int) -> None:
    """
    Downloads the PDF from the given URL and saves it to the contents directory.
    Skips download if file already exists.

    Args:
        pdf_url (str): The URL of the PDF to download
        step_id (int): The ID of the step for naming the file
    """
    file_path = prepare_file_path(file_name=f"content_{step_id}.pdf")

    # Decode the URL
    decoded_url = unquote(pdf_url)

    response = requests.get(decoded_url)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
    else:
        logging.error(f"Failed to download PDF for step {step_id}: Status code {response.status_code}")



def should_skip_if_exists(file_path: str) -> None:
    if os.path.exists(file_path):
        logging.info(f"{file_path} already exists, skipping the download/save")
        return
    pass


def get_pdf_url(scrapper: SeleniumScrapper) -> str:
    """
    Extracts the PDF URL from the iframe on the page.

    Args:
        scrapper (SeleniumScrapper): Instance of SeleniumScrapper to interact with the webpage

    Returns:
        str: The URL of the PDF if found, otherwise None
    """
    try:
        iframe = WebDriverWait(scrapper.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe.pdfrenderer'))
        )
        pdf_url = iframe.get_attribute('src')  # Get the src attribute which contains the PDF URL
        if 'file=' in pdf_url:
            return pdf_url.split('file=')[1]  # Extract the actual PDF URL
        return None
    except TimeoutException:
        logging.error("PDF iframe not found on page")
        return None


def process_step_text_content(scrapper: SeleniumScrapper, step: Step) -> Content:
    """
    Process and save the text content for a given step.

    Args:
        scrapper (SeleniumScrapper): Instance of SeleniumScrapper to interact with the webpage
        step (Step): Step object containing step metadata
        contents (list[Content]): List of existing content objects

    Returns:
        Content: The created content object

    Raises:
        Exception: If there are issues getting or saving the content
    """
    content, html = get_content_and_html_for_step(scrapper, step)
    if not content or not html:
        logging.error(f"Failed to get content for step {step.id}: Empty content or HTML")
        return None

    save_content_to_file(content, html)
    return content


def save_content_to_file(content: Content, html: str) -> None:
    """
    Saves HTML content to a file and appends the content object to the contents list.

    Args:
        content (Content): Content object containing metadata
        html (str): HTML content to save
    """
    file_path = prepare_file_path(file_name=content.filename)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
    except Exception as e:
        logging.error(f"Failed to save content file for step {content.step.id}: {str(e)}")


def navigate_to_step_module(scrapper: SeleniumScrapper, index: int) -> None:
    """
    Navigates to a specific step module by clicking on it.
    The step module have to be found again each time or they become stale.

    Args:
        scrapper (SeleniumScrapper): Instance of SeleniumScrapper
        index (int): Index of the step module to navigate to

    Returns:
        None
    """
    # Find and click the step module at the given index
    step_modules = scrapper.driver.find_elements(By.CSS_SELECTOR, SELECTORS['module_item'])
    step_modules[index].click()


def get_content_and_html_for_step(scrapper: SeleniumScrapper, step: Step) -> tuple[Content, str]:
    # Find the text content element
    try:
        # Wait up to 10 seconds for the text content element to be present on the page
        # The #textRender element contains the main content of each step
        text_content = WebDriverWait(scrapper.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#textRender'))
        )
    except Exception as e:
        logging.error(f"Failed to find text content element: {str(e)}")
        text_content = None

    content = Content(
        id=step.id,
        step=step,
        filename=f"content_{step.id}.html",
        type="text",
    )

    # Save HTML content to file
    try:
        html_content = text_content.get_attribute('innerHTML')
        return content, html_content
    except Exception as e:
        logging.error(f"Failed to save content for step {step.id}: {str(e)}")
        return None, None
    return None, None


def unblock_all_steps(scrapper: SeleniumScrapper, steps: list[Step]) -> None:
    """
    Unblocks all steps in a training module by navigating through them sequentially.

    Args:
        scrapper (SeleniumScrapper): Instance of SeleniumScrapper to interact with the webpage
        steps (list[Step]): List of Step objects to process

    Returns:
        None

    Raises:
        Exception: If step navigation fails
    """
    try:
        steps_to_unblock = get_steps_to_unblock(steps=steps)
        for step in steps_to_unblock:
            navigate_to_step_page(scrapper=scrapper, step=step)
    except Exception as e:
        logging.error(f"Failed to unblock steps: {str(e)}")
        raise


def navigate_to_step_page(scrapper: SeleniumScrapper, step: Step) -> None:
    """
    Navigates to a step's page.

    Args:
        scrapper (SeleniumScrapper): Instance of SeleniumScrapper to interact with the webpage
        step (Step): Step object containing the step information

    Raises:
        Exception: If navigation or page load fails
    """
    # Navigate to step page
    try:
        step_url = f"https://atelier-des-chefs.riseup.fr/Training/view/{step.training.id}/step/{step.platform_id}"
        logging.info(f"Navigating to step {step.platform_id} at {step_url}")
        scrapper.driver.get(step_url)

        # Wait for page load
        WebDriverWait(scrapper.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.training-view-module-item'))
        )
    except Exception as e:
        logging.error(f"Failed to navigate to step {step.platform_id}: {str(e)}")


def get_steps_to_unblock(steps: list[Step]) -> list[Step]:
    """
    Gets list of steps that we need to reach to unblock the next step. Starting from one before first blocked step.

    Args:
        steps (list[Step]): List of Step objects to process

    Returns:
        list[Step]: Filtered list of steps to process
    """
    # Find index of first blocked step
    first_blocked_idx = next((i for i, step in enumerate(steps) if step.is_blocked), len(steps))

    # Get steps from previous index to end
    return steps[max(0, first_blocked_idx-1):]

def prepare_file_path(base_dir: str = 'platform_new/contents', file_name: str = None) -> str:
    """
    Prepares the file path for video content and creates the directory if needed.

    Args:
        step_id (int): ID of the step
        base_dir (str): Base directory for content files
        file_name (str): Name of the file

    Returns:
        str: Complete file path for the video

    Raises:
        OSError: If directory creation fails
    """
    try:
        os.makedirs(base_dir, exist_ok=True)
        file_path = os.path.join(base_dir, file_name)
        if os.path.exists(file_path):
            logging.info(f"File already exists at {file_path}")
        return file_path
    except OSError as e:
        logging.error(f"Failed to create directory {base_dir}: {str(e)}")
        raise