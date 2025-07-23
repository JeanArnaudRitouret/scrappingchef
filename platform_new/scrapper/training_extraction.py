import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from platform_new.models.models import Training
from .logger import get_logger

# Create logger for this module
logger = get_logger(__name__)

# CSS selectors used for training extraction
TRAINING_SELECTORS = {
    'title': 'td:first-child .td-content-text .td-content-data .text-font-semi-bold',
    'progression': 'td[data-header="Progression"] .progress-bar__value',
    'score': 'td[data-header="Score"] .td-content-data div',
    'training_type': 'td:first-child .td-content-sub-data .text-size-small',
    'next_step': 'td[data-header="Étape suivante"] .td-content-data .text-font-semi-bold'
}


def build_trainings_from_card(card: WebElement, path_id: str) -> list[Training]:
    """
    Extracts training information from a path training card WebElement.

    Args:
        card (WebElement): The WebElement containing the path training card data
        path_id (str): The ID of the parent path

    Returns:
        list[Training]: List of Training objects containing the extracted information
    """
    try:
        # Wait for the card to be loaded, avoid timing issues when code is executed too fast
        time.sleep(3)
        # Check that card is open
        card_open_icon = card.find_element(By.CSS_SELECTOR, '.deploy--open')
        if card_open_icon is None:
            return []
        
        # Find training rows within the body of the card (training are table rows)
        card_body = card.find_element(By.CSS_SELECTOR, 'tbody')
        training_rows = card_body.find_elements(By.CSS_SELECTOR, 'tr')

        trainings = []
        for index, row in enumerate(training_rows):
            training = _build_training_from_row(row=row, path_id=path_id, index=index)
            # TODO: it's possible that the training was already built for another path, then we only need to add a new path_id
            trainings.append(training)

        return trainings

    except (NoSuchElementException) as e:
        logger.error(f"Could not locate training rows in card element: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while processing trainings: {str(e)}")
        return []


def _build_training_from_row(row: WebElement, path_id: str, index: int) -> Training:
    """
    Builds a Training object from a table row element.

    Args:
        row: WebElement representing the training row
        path_id: ID of the parent path
        index: Index of the training within the path

    Returns:
        Training object with extracted data
    """
    try:
        title = _extract_training_title(row)
        training_id = _create_training_id(title, path_id, index)
        progress = _extract_training_progress(row)
        score = _extract_training_score(row)
        training_type = _extract_training_type(row)

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
        logger.error(f"Failed to extract training data from row: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while building training: {str(e)}")
        raise


def _create_training_id(title: str, path_id: str, index: int) -> str:
    """
    Create a unique training ID from the training title, path ID, and index.
    
    Args:
        title: Training title as string
        path_id: Path ID as string
        index: Index of training within the path
        
    Returns:
        Unique training ID as string
    """
    # Create a unique identifier by combining title, path_id, and index
    # This ensures uniqueness even if titles are similar
    return f"training_{title.replace(' ', '_').replace('#', '').replace('-', '_')}_{path_id}_index_{index}"


def _extract_training_title(row: WebElement) -> str:
    """
    Extract training title from the row.
    
    Args:
        row: WebElement representing the training row
        
    Returns:
        Training title as string
    """
    title_element = row.find_element(By.CSS_SELECTOR, TRAINING_SELECTORS['title'])
    return title_element.text.strip()


def _extract_training_progress(row: WebElement) -> float:
    """
    Extract training progress from the first progression bar.
    
    Args:
        row: WebElement representing the training row
        
    Returns:
        Progress as float (0.0 to 1.0)
    """
    progression_elements = row.find_elements(
        By.CSS_SELECTOR,
        TRAINING_SELECTORS['progression']
    )
    
    # Get progress from first bar and convert to float, default to 0 if no value
    progress_text = progression_elements[0].text.strip('%')
    return float(progress_text if progress_text else '0') / 100


def _extract_training_score(row: WebElement) -> float | None:
    """
    Extract training score from the score column.
    
    Args:
        row: WebElement representing the training row
        
    Returns:
        Score as float (0.0 to 1.0) or 0 if not available
    """
    try:
        score_element = row.find_element(By.CSS_SELECTOR, TRAINING_SELECTORS['score'])
        score_text = score_element.text.strip()
        if score_text != '-' and score_text:
            try:
                return float(score_text.strip('%')) / 100
            except ValueError:
                return 0
    except NoSuchElementException:
        return 0
    
    return 0


def _extract_training_type(row: WebElement) -> str:
    """
    Extract training type from the sub-data text.
    
    Args:
        row: WebElement representing the training row
        
    Returns:
        Training type as string, or 'unknown' if not found
    """
    try:
        type_element = row.find_element(By.CSS_SELECTOR, TRAINING_SELECTORS['training_type'])
        return type_element.text.strip()
    except NoSuchElementException:
        return 'unknown'


