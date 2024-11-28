import os
from venv import logger
from dotenv import load_dotenv
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from platform_new.models import Path, Training, Step
from platform_new.scrapper.path_training_scrapping import get_scrapped_path_and_training_objects
from platform_new.scrapper.step_scrapping import get_scrapped_step_objects_for_training_module
from platform_new.scrapper.scrapper import SeleniumScrapper
from platform_new.decorators import local_environment_required
from scrappingchef.utils import _bulk_create_or_update
load_dotenv()

def index(request):
    return render(request, 'index.html')

@local_environment_required
def scrap_all_steps(request: HttpRequest) -> HttpResponse:
    try:
        scrapper = SeleniumScrapper()

        training_ids = Training.objects.values_list('id', flat=True)
        if not training_ids:
            return JsonResponse({"error": "No trainings found in database"}, status=404)

        scrapped_steps_objects = []
        for training_id in training_ids:
            steps = get_scrapped_step_objects_for_training_module(scrapper=scrapper, training_id=training_id)
            scrapped_steps_objects.extend(steps)

        if not scrapped_steps_objects:
            return JsonResponse({"error": "Failed to scrape any steps"}, status=503)

        _bulk_create_or_update(model_class=Step, objects=scrapped_steps_objects)

        context = {"steps": scrapped_steps_objects}
        return render(request, "platform_new/steps.html", context)

    except Exception as e:
        logger.error(f"Unexpected error in scrap_steps: {str(e)}")
        return JsonResponse({"error": "Scraping service temporarily unavailable"}, status=503)


def scrap_steps_for_training(request: HttpRequest, training_id: int) -> HttpResponse:
    try:
        scrapper = SeleniumScrapper()
        scrapped_steps_objects = get_scrapped_step_objects_for_training_module(scrapper=scrapper, training_id=training_id)
        _bulk_create_or_update(model_class=Step, objects=scrapped_steps_objects)
        context = {"steps": scrapped_steps_objects}
        return render(request, "platform_new/steps.html", context)
    except Exception as e:
        return JsonResponse({"error": "Scraping service temporarily unavailable"}, status=503)



@local_environment_required
def scrap_all_paths_and_trainings(
    request: HttpRequest
) -> HttpResponse:
    """
    Scrap all available paths and trainings, create or update them.
    Create the paths and trainings in the database if they don't exist, only update the fields if they already exist.
    Render the paths and trainings in a template.
    Args:
        request (Any | None, optional): Defaults to None.

    Returns:
        HttpResponse: object with a rendered text which is a combination of a template with a context dictionary
    """
    try:
        # Initialize the scrapper
        scrapper = SeleniumScrapper()

        # Get the path objects scrapped from the platform
        scrapped_path_objects, scrapped_training_objects = get_scrapped_path_and_training_objects(scrapper=scrapper)

        # Create or update the path objects in the database
        _bulk_create_or_update(model_class=Path, objects=scrapped_path_objects)

        # Create or update the training objects in the database
        _bulk_create_or_update(model_class=Training, objects=scrapped_training_objects)

        # Render both paths and trainings tables in the same template
        context = {
            "paths": scrapped_path_objects,
            "trainings": scrapped_training_objects
        }
        # Use paths_and_trainings.html template which will be followed by trainings.html template
        return render(request, "platform_new/paths_and_trainings.html", context)

    except Exception as e:
        # Log the error and return a friendly response
        print(f"Scraping error: {str(e)}")
        return JsonResponse({"error": "Scraping service temporarily unavailable"}, status=503)


def list_scrapped_paths(
    request: HttpRequest
) -> HttpResponse:
    """
    List all scrapped paths from the database.

    Args:
        request (HttpRequest): The HTTP request object

    Returns:
        HttpResponse: JSON response containing list of paths or error message

    Raises:
        Exception: If there's an error retrieving paths from database
    """
    try:
        # Get all paths and serialize them
        paths = Path.objects.all().values(
            'id',
            'platform_id',
            'title',
            'progression',
            'score',
            'created_time',
            'updated_time'
        )

        context = {"paths": paths}
        return render(request, "platform_new/paths.html", context)

    except Exception as e:
        # Log the error
        logger.error(f"Error retrieving paths: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": "An error occurred while retrieving paths"
        }, status=500)


def list_scrapped_trainings(
    request: HttpRequest
) -> HttpResponse:
    """
    List all scrapped trainings from the database.

    Args:
        request (HttpRequest): The HTTP request object

    Returns:
        HttpResponse: JSON response containing list of trainings or error message

    Raises:
        Exception: If there's an error retrieving trainings from database
    """
    try:
        # Get all trainings and serialize them
        trainings = Training.objects.all().values(
            'id',
            'platform_id',
            'path__title',
            'title',
            'progression',
            'score',
            'type',
            'created_time',
            'updated_time'
        )

        context = {"trainings": trainings}
        return render(request, "platform_new/trainings.html", context)

    except Exception as e:
        # Log the error
        logger.error(f"Error retrieving trainings: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": "An error occurred while retrieving trainings"
        }, status=500)


def list_scrapped_steps(request: HttpRequest) -> HttpResponse:
    try:
        steps = Step.objects.all().values(
            'id',
            'platform_id',
            'title',
            'training__id',
            'type',
            'is_validated',
            'is_blocked',
            'created_time',
            'updated_time',
        )

        context = {"steps": steps}
        return render(request, "platform_new/steps.html", context)

    except Exception as e:
        logger.error(f"Error retrieving steps: {str(e)}")
        return JsonResponse({"status": "error", "message": "An error occurred while retrieving steps"}, status=500)
