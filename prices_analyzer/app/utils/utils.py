# from concurrent.futures import ThreadPoolExecutor
from ..utils.logger import get_logger
import yaml


logger = get_logger(__name__)


def load_yaml_file(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {file_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML file {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error when loading YAML file {file_path}: {e}")
        raise




