import os

IMAGES_DIR = os.getenv("IMAGES_DIR")
if not IMAGES_DIR:
    raise ValueError("IMAGES_DIR environment variable must be set")

if not os.path.exists(IMAGES_DIR):
    raise ValueError(f"IMAGES_DIR {IMAGES_DIR} does not exist")

DB_PATH = os.path.join(IMAGES_DIR, "gallery.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
