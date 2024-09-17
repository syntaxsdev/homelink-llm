import yaml


def load_yaml(file_path: str):
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


