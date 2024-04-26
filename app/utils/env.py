from dotenv import load_dotenv
from loguru import logger
import os, sys

# Determine which environment to use (dev or prod)
from_arg = sys.argv[1] if len(sys.argv) > 1 else 'dev'
environment = os.getenv('ENVIRONMENT', from_arg)

match environment:
    case 'dev': dotenv_path = '.env.dev'
    case 'prod': dotenv_path = '.env.prod'
    case _: raise ValueError('Invalid environment specified')

# Load environment variables from the corresponding .env file
load_dotenv(dotenv_path)
logger.info(f"[env] loaded environment: {dotenv_path}")

# Define functions to access environment variables
def get_variable(name, default=None):
    return os.getenv(name, default)
