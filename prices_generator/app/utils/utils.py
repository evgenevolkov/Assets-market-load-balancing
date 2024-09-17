import os
import yaml
from ..utils.logger import get_logger

logger = get_logger(__name__)


def load_yaml_file(file_path: str) -> dict:
    """Reads yaml file."""
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


def get_config_filepath():
    """Helper function to get absolute price_config location."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_filepath = os.path.join(base_dir, 'config', 'price_config.yaml')
    return config_filepath







