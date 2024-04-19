import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define functions to access environment variables
def get_variable(name, default=None):
    return os.getenv(name, default)
