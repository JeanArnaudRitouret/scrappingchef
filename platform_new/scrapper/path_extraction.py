from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from platform_new.models.models import Path
from .logger import get_logger

# Create logger for this module
logger = get_logger(__name__)

# CSS selectors used for path extraction
PATH_SELECTORS = {
    'title': 'training-path-subscription-card__title',
    'progress_bars': '.progress-bar__value',
    'details_block': '.training-path-subscription-card__details-block',
}


def build_path_from_card(card: WebElement) -> Path:
    """
    Extracts path information from a path card WebElement.

    Args:
        card (WebElement): The WebElement containing the path card data

    Returns:
        Path: A Path object containing the extracted information

    Raises:
        NoSuchElementException: If required elements are not found in the card
        StaleElementReferenceException: If the card becomes stale
    """
    try:
        title = _extract_path_title(card)
        progression = _extract_path_progression(card)
        score = _extract_path_score(card)
        path_id = _generate_path_id(title)

        # Validate extracted data
        if title == '':
            raise ValueError(f"Path title cannot be empty. title='{title}'")
        
        return Path(
            id=path_id,
            platform_id=path_id,
            title=title,
            progression=progression,
            score=score
        )

    except (NoSuchElementException, StaleElementReferenceException) as e:
        logger.error(f"Failed to extract path data from card: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Invalid path data: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while building path: {str(e)}")
        raise 


def _extract_path_title(card: WebElement) -> str:
    """
    Extract path title from the card.
    
    Args:
        card: WebElement representing the path card
        
    Returns:
        Path title as string
    """
    title_element = card.find_element(By.CLASS_NAME, PATH_SELECTORS['title'])
    return title_element.text.strip()


def _extract_path_progression(card: WebElement) -> float:
    """
    Extract path progression from the first progress bar.
    
    Args:
        card: WebElement representing the path card
        
    Returns:
        Progression as float (0.0 to 1.0)
    """
    progress_bars = card.find_elements(By.CSS_SELECTOR, PATH_SELECTORS['progress_bars'])
    if len(progress_bars) > 0:
        progression_text = progress_bars[0].text.strip('%')
        return float(progression_text if progression_text else '0') / 100
    return 0.0


def _extract_path_score(card: WebElement) -> float:
    """
    Extract path score from the second progress bar.
    
    Args:
        card: WebElement representing the path card
        
    Returns:
        Score as float (0.0 to 1.0) or None if not available
    """
    progress_bars = card.find_elements(By.CSS_SELECTOR, PATH_SELECTORS['progress_bars'])
    if len(progress_bars) > 1:  # Second progress bar is the score
        score_text = progress_bars[1].text.strip('%')
        if score_text and score_text != '-':
            try:
                return float(score_text) / 100
            except ValueError:
                return 0.0
    return 0.0


def _generate_path_id(title: str) -> str:
    """
    Generate a unique path ID from the title.
    
    Args:
        title: Path title
        
    Returns:
        Generated path ID
    """
    return f"path_{title.replace(' ', '_').replace('#', '').replace('-', '_')}"

