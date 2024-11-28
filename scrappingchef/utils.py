import os


def loop_until_get(get_function, loop_limit, error_if_limit_reached=True, *args, **kwargs) -> any:
    """
    This function will call another function get_function until it returns a non-None value or the loop_limit is reached. 
    If the loop_limit is reached, it will raise an exception unless error_if_limit_reached is set to False.

    Args:
        get_function (_type_): should be a function that returns a value non-Null
        loop_limit (_type_): _description_
        error_if_limit_reached (bool, optional): _description_. Defaults to True.

    Raises:
        Exception: _description_

    Returns:
        _type_: _description_
    """
    for i in range(loop_limit):
        # check if the current loop iteration i is at a progress point (e.g., 10%, 20%, etc.)
        # and print the state of the progress point
        if (i % max(1, loop_limit // 10) == 0):
            print(f"loop_until_get for the function {get_function.__name__} on loop #{i}")

        get_results = get_function(*args, **kwargs)
        if get_results:
            return get_results

    if error_if_limit_reached:
        raise Exception(f"Error: Looped until limit reached without a result")
    else:
        return []


def loop_until_pass(pass_function, loop_limit, error_if_limit_reached=True, *args, **kwargs) -> bool:
    """
    This function will call another function pass_function until it doesn't return an error or the loop_limit is reached. 
    If the loop_limit is reached, it will raise an exception unless error_if_limit_reached is set to False.

    Args:
        pass_function (_type_): should be a function that returns a boolean value
        loop_limit (_type_): _description_
        error_if_limit_reached (bool, optional): _description_. Defaults to True.

    Raises:
        Exception: _description_

    Returns:
        _type_: _description_
    """
    is_passed = False
    for i in range(loop_limit):
        # check if the current loop iteration i is at a progress point (e.g., 10%, 20%, etc.)
        # and print the state of the progress point
        if (i % max(1, loop_limit // 10) == 0):
            print(f"loop_until_pass for the function {pass_function.__name__} on loop #{i}")

        try:
            pass_function(*args, **kwargs)
            is_passed=True
        except Exception as e:
            print(f"Error: {e}")
        if is_passed:
            return True

    if error_if_limit_reached:
        raise Exception(f"Error: Looped until limit reached without a result")
    else:
        return False

def check_if_folder_exists(folder_path=None, create_folder=True):
    if not os.path.exists(folder_path):
        if create_folder:
            os.makedirs(folder_path)
        return False
    return True


def _bulk_create_or_update(model_class, objects):
    """
    Helper function to perform bulk create or update operations.

    Args:
        model_class: Django model class (Path or Training)
        objects: List of objects to create/update
    """
    try:
        return model_class.objects.bulk_create(
            objs=objects,
            update_conflicts=True,
            update_fields=[
                field.__dict__.get('name')
                for field in model_class._meta.get_fields()
                if field.__dict__.get('primary_key') is False
            ],
            unique_fields=[
                field.__dict__.get('name')
                for field in model_class._meta.get_fields()
                if field.__dict__.get('primary_key')
            ]
        )
    except Exception as e:
        print(f"Error during bulk create/update for {model_class.__name__}: {str(e)}")
        return None