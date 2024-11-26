import logging
import os
import time
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from platform_new.models import Path, Training
from selenium.webdriver.remote.webelement import WebElement
from platform_new.scrapper.scrapper import SeleniumScrapper
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

load_dotenv()

# CSS selectors used for path and training scraping
SELECTORS = {
    'path': {
        'anchor': './preceding-sibling::div[@class="pathtraining-anchor"]',
        'header': 'pathtraining-header',
        'title': 'pathtraining-header-title',
        'progression': '.pathtraining-header-progress .pathtraining-table-column-progress-value.text-primarycolor',
        'score': '.pathtraining-header-progress-score .pathtraining-table-column-progress-value.text-primarycolor',
    },
    'training': {
        'rows': '.pathtraining-table-data',
        'link': '.pathtraining-action-main-button a',
        'title': '.pathtraining-table-column-trainings-title',
        'progression': '.rup-table-progress .progress-bar-value',
        'illustration': '.illustration'
    }
}


def get_scrapped_path_and_training_objects(scrapper: SeleniumScrapper) -> tuple[list[Path], list[Training]]:
    """
    Scrapes path and training objects from all pages of the training platform.

    Args:
        scrapper: SeleniumScrapper instance to interact with the webpage

    Returns:
        List of Path objects containing scraped data

    Raises:
        WebDriverException: If there are issues accessing the webpage
    """
    try:
        # Navigate to training paths page
        scrapper.driver.get(os.environ['URL_NEW_PLATFORM_TRAINING'])

        num_pages = get_number_of_pages_for_paths(scrapper=scrapper)

        scrapped_path_objects: list[Path] = []
        scrapped_training_objects: list[Training] = []

        # Process each page and navigate to next page if available
        for page in range(1, num_pages + 1):
            paths_from_page, trainings_from_page = scrap_paths_and_trainings_from_single_page(
                scrapper=scrapper,
                page=page
            )
            scrapped_path_objects.extend(paths_from_page)
            scrapped_training_objects.extend(trainings_from_page)

            has_next_page = navigate_to_next_page(
                scrapper=scrapper,
                page=page,
                num_pages=num_pages
            )

            if not has_next_page:
                break

        return scrapped_path_objects, scrapped_training_objects

    except Exception as e:
        print(f"Failed to scrape path objects: {str(e)}")
        return [], []


def scrap_paths_and_trainings_from_single_page(scrapper: SeleniumScrapper, page: int) -> tuple[list[Path], list[Training]]:
    """
    Process a single page of path and training objects.

    Args:
        scrapper: SeleniumScrapper instance
        page: Current page number being processed

    Returns:
        List of Path objects and Training objects from the current page
    """
    try:
        # Find all path training cards on current page
        pathtraining_cards = scrapper.driver.find_elements(
            By.CSS_SELECTOR,
            '.pathtraining-card'
        )

        # Extract path data from each path training card
        paths_on_page = []
        trainings_on_page = []
        for card in pathtraining_cards:
            try:
                path = build_path_from_pathtraining_card(card=card)
                paths_on_page.append(path)
                trainings = build_trainings_from_pathtraining_card(card=card, path_id=path.id)
                trainings_on_page.extend(trainings)
            except Exception as e:
                logging.error(f"Failed to process card: {e}")
                continue

        return paths_on_page, trainings_on_page

    except Exception as e:
        print(f"Error processing page {page}: {str(e)}")
        return [], []


def build_path_from_pathtraining_card(card: WebElement) -> Path:
    """
    Extracts path information from a pathtraining card WebElement.

    Args:
        card (WebElement): The WebElement containing the pathtraining card data

    Returns:
        Path: A Path object containing the extracted information

    Raises:
        NoSuchElementException: If required elements are not found in the card
        StaleElementReferenceException: If the card becomes stale
    """
    try:
        # Get the associated ID from the preceding pathtraining-anchor
        anchor_id = card.find_element(
            By.XPATH,
            SELECTORS['path']['anchor']
        ).get_attribute('id')

        if not anchor_id:
            raise ValueError("Anchor ID cannot be empty")

        # Find the header inside the card
        header = card.find_element(
            By.CLASS_NAME,
            SELECTORS['path']['header']
        )

        # Extract title, progression and score from header
        header_title = header.find_element(By.CLASS_NAME, SELECTORS['path']['title']).text.strip()
        progression = float(header.find_element(By.CSS_SELECTOR, SELECTORS['path']['progression']).text.strip('%')) / 100
        score = float(header.find_element(By.CSS_SELECTOR, SELECTORS['path']['score']).text.strip('%')) / 100

        # Validate extracted data
        if header_title == '' or progression is None or score is None:
            raise ValueError(f"All path attributes must have non-empty values. title='{header_title}', progression={progression}, score={score}")

        return Path(
            id=anchor_id,
            platform_id=anchor_id,
            title=header_title,
            progression=progression,
            score=score
        )

    except (NoSuchElementException, StaleElementReferenceException) as e:
        logging.error(f"Failed to extract path data from card: {str(e)}")
        raise
    except ValueError as e:
        logging.error(f"Invalid path data: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error while building path: {str(e)}")
        raise


def build_trainings_from_pathtraining_card(card: WebElement, path_id: str) -> list[Training]:
    """
    Extracts training information from a pathtraining card WebElement.

    Args:
        card (WebElement): The WebElement containing the pathtraining card data
        path_id (str): The ID of the parent path

    Returns:
        list[Training]: List of Training objects containing the extracted information
    """
    try:
        # No need to extract path_id again
        training_rows = card.find_elements(By.CSS_SELECTOR, SELECTORS['training']['rows'])

        trainings = []
        for row in training_rows:
            training = build_training_from_row(row=row, path_id=path_id)
            trainings.append(training)

        return trainings

    except (NoSuchElementException, StaleElementReferenceException) as e:
        logging.error(f"Failed to extract trainings from card: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error while processing trainings: {str(e)}")
        return []


def build_training_from_row(row: WebElement, path_id: str) -> Training:
    """
    Builds a Training object from a table row element.

    Args:
        row: WebElement representing the training row
        path_id: ID of the parent path

    Returns:
        Training object with extracted data
    """
    try:
        # Extract training ID from the link href
        training_link = row.find_element(By.CSS_SELECTOR, SELECTORS['training']['link'])
        href = training_link.get_attribute('href')
        training_id = href.split('/Training/view/')[1].split('/')[0]

        # Get the title element
        title_element = row.find_element(By.CSS_SELECTOR, SELECTORS['training']['title'])
        # Try different methods to get the text content
        title = (
            # First try the title attribute
            title_element.get_attribute('title')
            # or fall back to text
            or title_element.text.strip()
        )

        # Extract progress and score from progression bars
        progression_elements = row.find_elements(
            By.CSS_SELECTOR,
            SELECTORS['training']['progression']
        )

        # Get progress from first bar and convert to float, default to 0 if no value
        progress_text = progression_elements[0].text.strip('%')
        progress = float(progress_text if progress_text else '0') / 100

        # Get score from second bar if it exists
        score = None
        if len(progression_elements) > 1:
            score_text = progression_elements[1].text.strip()
            if score_text != '-':
                score = float(score_text.strip('%')) / 100

        # Extract training type from the illustration class
        illustration_element = row.find_element(By.CSS_SELECTOR, SELECTORS['training']['illustration'])
        illustration_classes = illustration_element.get_attribute('class').split()

        # Find the class that starts with 'illustration-' (excluding the base 'illustration' and 'illustration-md' classes)
        training_type = next(
            (cls.replace('illustration-', '')
             for cls in illustration_classes
             if cls.startswith('illustration-') and cls not in ['illustration', 'illustration-md']),
            'unknown'  # Default value if no matching class is found
        )

        return Training(
            id=training_id,
            platform_id=training_id,
            path_id=path_id,
            title=title,
            progression=progress,
            type=training_type,
            score=score
        )
    except (NoSuchElementException, StaleElementReferenceException, ValueError) as e:
        logging.error(f"Failed to extract training data from row: {str(e)}")
        breakpoint()
        raise
    except Exception as e:
        logging.error(f"Unexpected error while building training: {str(e)}")
        raise



def get_number_of_pages_for_paths(scrapper: SeleniumScrapper) -> int:
    """
    Get the number of pages in the pagination.
    Args:
        scrapper (SeleniumScrapper): An instance of our custom SeleniumScrapper class.

    Returns:
        int: The number of pages in the pagination.
    """
    # Locate the pagination element
    pagination = scrapper.driver.find_element(By.CLASS_NAME, "pagination")

    # Find all the page items inside the pagination
    page_items = pagination.find_elements(By.CLASS_NAME, "page-item")

    # Extract the page numbers from the 'data-page' attribute or inner text
    page_numbers = []
    for item in page_items:
        try:
            page_number = item.find_element(By.CLASS_NAME, "page-link").get_attribute("data-page")
            if page_number is not None:
                page_numbers.append(int(page_number))
        except:
            pass

    # Get the number of pages as maximum page
    num_pages = max(page_numbers) if page_numbers else 0
    return num_pages


def navigate_to_next_page(
    scrapper: SeleniumScrapper,
    page: int,
    num_pages: int
) -> bool:
    """
    Navigate to the next page in the pagination if available.

    Args:
        scrapper (SeleniumScrapper): Selenium scrapper instance
        page (int): Current page number
        num_pages (int): Total number of pages

    Returns:
        bool: True if successfully navigated to next page, False otherwise

    Raises:
        TimeoutException: If next page does not load within timeout
        NoSuchElementException: If next button is not found
    """
    # If current page is the last page, return False
    if page >= num_pages:
        return False

    try:
        # Locate and click the "Next" button with explicit wait
        next_button = WebDriverWait(scrapper.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'li.page-item a.js-page-next'))
        )

        # Scroll into view and click using JavaScript for reliability
        scrapper.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        scrapper.driver.execute_script("arguments[0].click();", next_button)

        # Wait for next page to load and verify correct page number
        WebDriverWait(scrapper.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'li.page-item.active a[data-page="{page + 1}"]'))
        )

        # Add small delay to ensure page content is loaded
        time.sleep(1)
        return True

    except TimeoutException as e:
        logging.error(f"Timeout while navigating to page {page + 1}: {str(e)}")
        return False

    except NoSuchElementException as e:
        logging.error(f"Next button not found on page {page}: {str(e)}")
        return False

    except Exception as e:
        logging.error(f"Unexpected error navigating to page {page + 1}: {str(e)}")
        return False


