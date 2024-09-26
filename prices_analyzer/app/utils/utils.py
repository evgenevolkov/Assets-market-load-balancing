""" Utility function module"""
from ..utils.logger import get_logger
import yaml


logger = get_logger(__name__)


def load_yaml_file(file_path: str) -> dict:
    """gracefully reads and parses yaml file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}, error: {e}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML file {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error when loading YAML file {file_path}: {e}")
        raise




