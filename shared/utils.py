import yaml
from datetime import datetime
from time import time
class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

def load_yaml(file_path: str) -> dict:
    """
    Loads a yaml file

    Args:
        file_path: the file location"""
    with open(file_path, "r") as file:
        try:
            data = yaml.safe_load(file)
            return data
        except yaml.YAMLError as exc:
            print(f"Error reading YAML file: {exc}")
            return None


def get_time() -> float:
    """
    Get the current time
    """
    return time()

def get_datetime() -> datetime:
    """
    Get the current datetime
    """
    return datetime.now()
