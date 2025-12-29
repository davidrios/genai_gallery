import os

# Define the images directory, defaulting to a sibling 'images' directory
# Can be overridden by IMAGES_DIR environment variable
DEFAULT_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images")
IMAGES_DIR = os.getenv("IMAGES_DIR", DEFAULT_IMAGES_DIR)

# Ensure the directory exists
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR, exist_ok=True)

# Database file location
DB_PATH = os.path.join(IMAGES_DIR, "gallery.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
