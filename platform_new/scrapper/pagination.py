import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from platform_new.scrapper.scrapper import SeleniumScrapper
from .logger import get_logger

# Create logger for this module
logger = get_logger(__name__)


def _extract_page_numbers_from_pagination(pagination: WebElement) -> list[int]:
    """
    Extract page numbers from pagination elements.
    
    Args:
        pagination: WebElement containing pagination controls
        
    Returns:
        List of page numbers as integers
    """
    page_numbers = []
    page_items = pagination.find_elements(By.CLASS_NAME, "page-item")
    
    for item in page_items:
        try:
            page_link = item.find_element(By.CLASS_NAME, "page-link")
            # Get the text content of the link
            link_text = page_link.text.strip()
            
            # Check if the text is a number (not an icon)
            if link_text and link_text.isdigit():
                page_numbers.append(int(link_text))
        except Exception:
            # Skip items that don't have valid page numbers
            pass
    
    return page_numbers


def get_number_of_pages_for_paths(scrapper: SeleniumScrapper) -> int:
    """
    Get the number of pages in the pagination.
    Args:
        scrapper (SeleniumScrapper): An instance of our custom SeleniumScrapper class.

    Returns:
        int: The number of pages in the pagination.
    """
    # Locate the pagination element
    if scrapper.driver is None:
        raise RuntimeError("Driver is not initialized")
    
    # Wait until at least 3 page items are found (the 2 chevrons and at least 1 page number)
    WebDriverWait(scrapper.driver, 10).until(
        lambda driver: len(driver.find_elements(By.CLASS_NAME, "page-item")) >= 3
    )
    
    pagination = scrapper.driver.find_element(By.CLASS_NAME, "pagination")

    page_numbers = _extract_page_numbers_from_pagination(pagination=pagination)
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
        logger.info(f"Navigating to next page {page + 1}")
        if scrapper.driver is None:
            raise RuntimeError("Driver is not initialized")

        # Look for the next button (chevron-right icon) and get its parent link
        next_icon = WebDriverWait(scrapper.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'li.page-item a.page-link i.fas.fa-chevron-right'))
        )
        next_button = next_icon.find_element(By.XPATH, './..')  # Get the parent <a> element

        # Scroll into view and click using JavaScript for reliability
        scrapper.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        scrapper.driver.execute_script("arguments[0].click();", next_button)

        # Wait for next page to load and verify correct page number
        # This lambda function checks that:
        # 1. The active page element exists (li.page-item.active a.page-link)
        # 2. The text content of the active element matches the expected page number (page + 1)
        # 3. Returns True only when both conditions are met, otherwise continues waiting
        # 4. Raises TimeoutException after 30 seconds if condition is never met
        WebDriverWait(scrapper.driver, 30).until(
            lambda driver: driver.find_element(By.CSS_SELECTOR, 'li.page-item.active a.page-link').text.strip() == str(page + 1)
        )
        logger.info(f"Next page {page + 1} loaded")

        # Add small delay to ensure page content is loaded
        time.sleep(1)
        return True

    except TimeoutException as e:
        logger.error(f"Timeout while navigating to page {page + 1}: {str(e)}")
        return False

    except NoSuchElementException as e:
        logger.error(f"Next button not found on page {page}: {str(e)}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error navigating to page {page + 1}: {str(e)}")
        return False 