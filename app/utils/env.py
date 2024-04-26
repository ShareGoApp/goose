from dotenv import load_dotenv
from loguru import logger
import os

# Determine which environment to use (dev or prod)
environment = os.getenv('ENVIRONMENT', 'prod')

match environment:
    case 'dev':
        dotenv_path = '.env.dev'
        logger.warning(f"[env] loaded environment: {dotenv_path}")
    case 'prod':
        dotenv_path = '.env.prod'
        logger.info(f"[env] loaded environment: {dotenv_path}")
    case _:
        raise ValueError('Invalid environment specified')

# Load environment variables from the corresponding .env file
load_dotenv(dotenv_path)


# Define functions to access environment variables
def get_variable(name, default=None):
    return os.getenv(name, default)
