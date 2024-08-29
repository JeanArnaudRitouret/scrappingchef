import os


def loop_until_get(get_function, loop_limit, error_if_limit_reached=True, *args, **kwargs):
    for i in range(loop_limit):
        if i%(int(loop_limit/10)) == 0:
            print(f"loop_until_get on loop #{i}")
        get_results = get_function(*args, **kwargs)
        if get_results:
            return get_results
    if error_if_limit_reached:
        raise Exception(f"Error: Looped until limit reached without a result")
    else:
        return []


def check_if_folder_exists(folder_path=None, create_folder=True):
    if not os.path.exists(folder_path):
        if create_folder:
            os.makedirs(folder_path)
        return False
    return True