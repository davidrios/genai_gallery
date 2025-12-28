import os
import hashlib
from datetime import datetime
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
def list_images(sort: str = "desc", db: Session = Depends(get_db)):
    sync_images(db)
    
    query = db.query(models.Image)
    if sort == "asc":
        query = query.order_by(models.Image.created_at.asc())
    else:
        query = query.order_by(models.Image.created_at.desc())
        
    images = query.all()
    return images

@app.get("/api/images/{image_id}")
def get_image_details(image_id: str, db: Session = Depends(get_db)):
    image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@app.get("/api/browse")
def browse(path: str = "", sort: str = "desc", db: Session = Depends(get_db)):
    # Security check to prevent path traversal
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # Ensure clean relative path (empty string for root)
    path = path.strip("/")
    
    full_path = os.path.join(IMAGES_DIR, path)
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
         raise HTTPException(status_code=404, detail="Directory not found")

    sync_images(db)

    # List subdirectories
    directories = []
    try:
        with os.scandir(full_path) as it:
            for entry in it:
                if entry.is_dir() and not entry.name.startswith('.'):
                    directories.append({
                        "name": entry.name,
                        "path": os.path.join(path, entry.name) if path else entry.name
                    })
    except OSError:
        pass
    
    directories.sort(key=lambda x: x["name"])

    # List images in this directory (from DB)
    query = db.query(models.Image)
    
    # Filter by parent directory
    # We want images whose relative path's dirname matches 'path'
    # Since DB usage of functions can be tricky across different DBs, we'll fetch wider or filter in python?
    # Actually, SQLite 'LIKE' is simpler.
    # Root: path has no slashes.
    # Subdir: path starts with 'subdir/' and has no more slashes after that.
    
    if sort == "asc":
        query = query.order_by(models.Image.created_at.asc())
    else:
        query = query.order_by(models.Image.created_at.desc())

    all_images = query.all()
    
    # Filter in python for simplicity and reliability with path strings
    # This might be slow if 100k images, but ok for personal gallery.
    # Optimization: Filter by prefix in SQL first if not root.
    
    results = []
    for img in all_images:
        img_dir = os.path.dirname(img.path)
        # Normalize for comparison
        if img_dir == path:
            results.append(img)
            
    return {
        "directories": directories,
        "images": results
    }

def calculate_sha1(filepath: str) -> str:
    sha1 = hashlib.sha1()
    try:
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                sha1.update(data)
        return sha1.hexdigest()
    except IOError:
        return None

def sync_images(db: Session):
    existing_images = {img.id: img for img in db.query(models.Image).all()}
    
    # Walk directory
    for root, dirs, files in os.walk(IMAGES_DIR):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, IMAGES_DIR)
                
                # Get modification time
                mtime = os.path.getmtime(full_path)
                created_at = datetime.fromtimestamp(mtime)

                # Calculate Hash
                file_hash = calculate_sha1(full_path)
                if not file_hash:
                    continue
                
                if file_hash not in existing_images:
                    # New image
                    db_image = models.Image(id=file_hash, path=rel_path, created_at=created_at)
                    db.add(db_image)
                else:
                    # Existing image: check path
                    existing_img = existing_images[file_hash]
                    
                    # Update mtime if needed (though sha1 is same, mtime might be what we want as "created_at" source of truth)
                    if existing_img.created_at != created_at:
                         existing_img.created_at = created_at
                         db.add(existing_img)

                    if existing_img.path != rel_path:
                        # Path mismatch. Check if old path is invalid (doesn't exist)
                        old_full_path = os.path.join(IMAGES_DIR, existing_img.path)
                        if not os.path.exists(old_full_path):
                            # Old path gone, update to new path
                            existing_img.path = rel_path
                            db.add(existing_img)
                        # Else: duplicate content. We keep the old path as canonical for now.
    
    db.commit()
