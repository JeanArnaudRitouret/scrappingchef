import logging
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from platform_new.scrapper.scrapper import SeleniumScrapper
from platform_new.models.models import Step, Training

# CSS selectors used for step scraping
SELECTORS = {
    'module_item': '.training-view-module-item',
    'title': '.training-view-module-item-title', 
    'state': '.training-view-module-item-state .state-box',
    'icon': '.item-icon-picto i'
}


def get_scrapped_step_objects_for_training_module(scrapper: SeleniumScrapper, training_id: int) -> list[Step]:
    """
    Scrapes step objects from the training modules.

    Args:
        scrapper (SeleniumScrapper): Instance of SeleniumScrapper to interact with the webpage
        training_id (int): ID of the training to scrape steps from

    Returns:
        list[Step]: List of Step objects containing the scraped data

    Raises:
        WebDriverException: If there are issues accessing the webpage
        NoSuchElementException: If required elements are not found
        StaleElementReferenceException: If elements become stale
    """
    # Replace the navigation code with the new function call
    if not navigate_to_training_page(scrapper, training_id):
        return []
    try:
        # Find all step module items
        module_items = scrapper.driver.find_elements(By.CSS_SELECTOR, SELECTORS['module_item'])

        # Process each module item to create a step object
        steps = process_module_items(module_items, training_id)

        return steps

    except Exception as e:
        logging.error(f"Error scraping steps: {str(e)}")
        return []


def navigate_to_training_page(scrapper: SeleniumScrapper, training_id: int) -> bool:
    """
    Navigates to the training view page and waits for module items to load.

    Args:
        scrapper (SeleniumScrapper): Instance of SeleniumScrapper
        training_id (int): ID of the training to navigate to

    Returns:
        bool: True if navigation was successful, False otherwise
    """
    try:
        # Navigate to training view page
        scrapper.driver.get(os.environ['URL_NEW_PLATFORM_TRAINING'] + f"/view/{training_id}/")

        # Wait for the training module items to load
        WebDriverWait(scrapper.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.training-view-module-item'))
        )
        return True

    except Exception as e:
        logging.error(f"Failed to navigate to training page {training_id}: {str(e)}")
        return False


def process_module_items(module_items, training_id):
    steps = []
    for index, item in enumerate(module_items):
        try:
            step = create_step_object(item, training_id, index)
            steps.append(step)
        except Exception as e:
            logging.error(f"Failed to process step item: {e}")
            continue
    return steps


def create_step_object(item, training_id: int, index: int) -> Step:
    # Extract the title
    title_element = item.find_element(By.CSS_SELECTOR, SELECTORS['title'])
    title = title_element.get_attribute('title') or title_element.text.strip()

    # Extract step ID from the href attribute after 'step/' and remove any query parameters
    href = item.get_attribute('href')
    try:
        step_id = int(href.split('/step/')[-1].split('?')[0])
    except (ValueError, AttributeError, IndexError) as e:
        raise ValueError(f"Failed to extract valid step ID from href '{href}' for training {training_id}: {str(e)}")

    # Extract the type from the icon
    icon_element = item.find_element(By.CSS_SELECTOR, '.item-icon-picto i')
    icon_classes = icon_element.get_attribute('class').split()
    step_type = next((cls.replace('icon-module-', '') for cls in icon_classes if cls.startswith('icon-module-')), 'unknown')

    # Extract the validation state
    state_element = item.find_element(By.CSS_SELECTOR, '.training-view-module-item-state .state-box')
    is_step_validated = 'state-success' in state_element.get_attribute('class')

    # Extract the blocked state
    is_step_blocked = 'state-locked' in state_element.get_attribute('class')

    # Create Step object
    step = Step(
        id=step_id,
        platform_id=step_id,
        training_id=training_id,
        title=title,
        type=step_type,
        is_validated=is_step_validated,
        is_blocked=is_step_blocked
    )

    return step