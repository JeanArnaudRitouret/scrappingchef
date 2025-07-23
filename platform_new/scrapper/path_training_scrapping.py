import os
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from platform_new.models.models import Path, Training
from platform_new.scrapper.scrapper import SeleniumScrapper

# Import the new modules
from .path_extraction import build_path_from_card
from .training_extraction import build_trainings_from_card
from .pagination import get_number_of_pages_for_paths, navigate_to_next_page
from .logger import get_logger

# Create logger for this module
logger = get_logger(__name__)


def get_scrapped_path_and_training_objects(scrapper: SeleniumScrapper) -> tuple[list[Path], list[Training]]:
    """
    Scrapping path and training objects from all pages of the training platform.
    Path are the highest level objects which contain a list of trainings. 
    Trainings are lower level objects which contain a list of steps.

    Args:
        scrapper: SeleniumScrapper instance to interact with the webpage

    Returns:
        A tuple containing a list of Path objects and a list of Training objects made from scraped data

    Raises:
        WebDriverException: If there are issues accessing the webpage
    """
    try:
        # Navigate to training paths page with retry logic
        if scrapper.driver is None:
            raise RuntimeError("Driver is not initialized")
        
        expected_url = os.environ['URL_NEW_PLATFORM_TRAINING_PATHS']
        
        if not navigate_to_page(scrapper=scrapper, url=expected_url):
            raise RuntimeError("Failed to reach training paths page")

        num_pages = get_number_of_pages_for_paths(scrapper=scrapper)

        scrapped_path_objects, scrapped_training_objects = _scrap_paths_and_trainings_from_all_pages(
            scrapper=scrapper,
            num_pages=num_pages
        )

        return scrapped_path_objects, scrapped_training_objects

    except Exception as e:
        logger.error(f"Failed to scrape path objects: {str(e)}")
        return [], []


def navigate_to_page(scrapper: SeleniumScrapper, url: str, max_attempts: int = 10, delay: int = 3) -> bool:
    """
    Navigate to a page with retry logic.
    
    Args:
        scrapper: SeleniumScrapper instance
        url: The URL to navigate to
        max_attempts: Maximum number of attempts (default: 10)
        delay: Delay between attempts in seconds (default: 3)
        
    Returns:
        True if navigation successful, False otherwise
    """
    if scrapper.driver is None:
        logger.error("Driver is not initialized")
        return False
        
    for attempt in range(max_attempts):
        logger.info(f"Navigating to {url} (attempt {attempt + 1}/{max_attempts})")
        scrapper.driver.get(url)
        time.sleep(delay)
        
        # Check if we're actually on the expected page
        current_url = scrapper.driver.current_url
        if current_url == url:
            logger.info(f"Successfully navigated to {url}")
            return True
        else:
            logger.warning(f"Navigation failed, expected {url} but got {current_url}")
    
    logger.error(f"Failed to navigate to {url} after {max_attempts} attempts")
    return False


def _scrap_paths_and_trainings_from_all_pages(scrapper: SeleniumScrapper, num_pages: int) -> tuple[list[Path], list[Training]]:
    """
    Process all pages in order to collect path and training objects from each page.
    
    Args:
        scrapper: SeleniumScrapper instance
        num_pages: Total number of pages to process
        
    Returns:
        Tuple of (list[Path], list[Training]) containing all scraped objects
    """
    scrapped_path_objects: list[Path] = []
    scrapped_training_objects: list[Training] = []

    # Process each page and navigate to next page if available
    for page in range(1, num_pages + 1):
        logger.info(f"Processing page {page}")
        paths_from_page, trainings_from_page = _scrap_paths_and_trainings_from_single_page(
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


def _scrap_paths_and_trainings_from_single_page(scrapper: SeleniumScrapper, page: int) -> tuple[list[Path], list[Training]]:
    """
    Process a single page of path and training objects.

    Args:
        scrapper: SeleniumScrapper instance
        page: Current page number being processed

    Returns:
        List of Path objects and Training objects from the current page
    """
    try:
        # Find all path training cards on current page and open them
        cards = _find_and_open_cards_on_page(scrapper)

        # Extract path data from each path training card
        paths_on_page = []
        trainings_on_page = []
        for card in cards:
            try:
                path = build_path_from_card(card=card)
                logger.info(f"Path {path.id} extracted from card")
                paths_on_page.append(path)
                trainings = build_trainings_from_card(card=card, path_id=str(path.id))
                logger.info(f"Trainings {trainings} extracted from card")
                trainings_on_page.extend(trainings)

            except Exception as e:
                logger.error(f"Failed to process card: {e}")
                continue

        return paths_on_page, trainings_on_page

    except Exception as e:
        logger.error(f"Error processing page {page}: {str(e)}")
        return [], []


def _find_and_open_cards_on_page(scrapper: SeleniumScrapper) -> list:
    """
    Find all training path cards on the current page and open them if they're closed.
    
    Args:
        scrapper: SeleniumScrapper instance
        
    Returns:
        List of card WebElements
    """
    if scrapper.driver is None:
        raise RuntimeError("Driver is not initialized")
    
    # Wait for the page to load
    time.sleep(3)

    # Each card is a path with multiple trainings
    cards = scrapper.driver.find_elements(
        By.CSS_SELECTOR,
        '.training-path-subscription-card'
    )

    # Make sure that cards are open - otherwise open them by clicking on the card
    for card in cards:
        try:
            open_card_icon = card.find_elements(By.CSS_SELECTOR, '.deploy--open')
            if not open_card_icon:
                # Wait for the chevron icon to be present and clickable
                WebDriverWait(scrapper.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.training-path-subscription-card__deploy-icon'))
                )
                
                chevron_icon = card.find_element(
                    By.CSS_SELECTOR,
                    '.training-path-subscription-card__deploy-icon'
                )

                scrapper.driver.execute_script("arguments[0].click();", chevron_icon)
                
        except Exception as e:
            logger.error(f"Failed to process card: {e}")
            continue

    open_cards = scrapper.driver.find_elements(
        By.CSS_SELECTOR,
        '.training-path-subscription-card'
    )
    return open_cards

