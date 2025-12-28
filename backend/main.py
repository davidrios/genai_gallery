import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models
import database
from database import engine, get_db
from config import IMAGES_DIR

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount images directory to serve static files
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

@app.get("/api/images")
def list_images(db: Session = Depends(get_db)):
    # Simple sync logic: scan directory and update DB
    # In a real app, this should be a background task or watcher
    # For now, we'll just return what's in the DB, but populate it if empty or upon request?
    # Let's do a quick scan to sync for this MVC
    sync_images(db)
    images = db.query(models.Image).order_by(models.Image.created_at.desc()).all()
    return images

def sync_images(db: Session):
    # Scan directory
    fs_files = set()
    for root, dirs, files in os.walk(IMAGES_DIR):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                fs_files.add(file)
    
    # Check DB
    db_images = db.query(models.Image).all()
    db_filenames = {img.filename for img in db_images}

    # Add new
    new_files = fs_files - db_filenames
    for filename in new_files:
        db_image = models.Image(filename=filename, path=os.path.join(IMAGES_DIR, filename))
        db.add(db_image)
    
    # Remove missing (optional, maybe we want to keep history? leaving for now)
    
    db.commit()

@app.get("/api/images/{filename}")
def get_image_details(filename: str, db: Session = Depends(get_db)):
    image = db.query(models.Image).filter(models.Image.filename == filename).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image
