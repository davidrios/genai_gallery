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

    db.commit()

def extract_metadata(filepath: str) -> dict:
    """
    Extracts ComfyUI Prompt metadata from PNG files.
    Returns a dict of flattened key-value pairs.
    """
    try:
        from PIL import Image
        with Image.open(filepath) as img:
            # ComfyUI often stores prompt in 'prompt' or 'workflow' text chunks
            # We are interested in 'prompt' which contains the inputs
            meta = img.info
            prompt_json = meta.get('prompt')
            if not prompt_json:
                return {}
            
            import json
            data = json.loads(prompt_json)
            
            flattened = {}
            
            # Helper to check if value is scalar
            def is_scalar(v):
                return isinstance(v, (str, int, float, bool)) and v is not None

            # Flatten inputs
            # Structure: { <node_id>: { "inputs": { ... }, "class_type": ... }, ... }
            for node_id, node_data in data.items():
                inputs = node_data.get('inputs', {})
                for key, value in inputs.items():
                    # Ignore 'type' and 'device' as per user request
                    # Also ignoring non-scalar values (lists, dicts are usually connections/arrays we don't need for simple search)
                    if key in ('type', 'device'):
                        continue
                    
                    if is_scalar(value):
                        # Key format: inputs.<key>
                        # But wait, user example: inputs.clip_name
                        # If multiple nodes have same input key, we might have collisions or duplicates.
                        # For a gallery search, maybe just key=value is enough?
                        # User asked for "inputs.clip_name" -> "qwen_3_4b.safetensors"
                        # This implies we lose context of which node it belonged to?
                        # Or maybe we prefix with node class type?
                        # User example:
                        # {"inputs": {"clip_name": "...", ...}, ...} -> inputs.clip_name
                        # If there are multiple nodes with 'clip_name', we will just capture all of them.
                        # We will start with strict "inputs.<key>"
                        
                        db_key = f"inputs.{key}"
                        # We might overwrite if multiple nodes have same param. 
                        # But user asked for "save in the database A KEY named inputs.clip_name"
                        # This implies uniqueness or multimap.
                        # Our ImageMetadata table allows multiple rows for same image.
                        # But 'key' is just a string.
                        # We will store: key="inputs.clip_name", value="qwen..."
                        # If multiple nodes have it, we store multiple rows? 
                        # Our model has separate Id for every metadata item, so yes we can store duplicates.
                        
                        # Let's start with just storing them.
                        # Optimization: maybe unique set?
                        flattened_key = f"inputs.{key}"
                        
                        # We store as list of tuples locally to handle duplicates?
                        # But dictionary key overrides.
                        # If I have 2 LoadCheckpoints, both have 'ckpt_name'.
                        # If I use dict, I lose one.
                        # Should I use a list?
                        # The function signature says return dict so far.
                        # Let's verify what user wants. "save in the database a key named inputs.clip_name"
                        # If I have two, maybe saving one is enough, or maybe I should accumulate.
                        # Let's accumulate into a list of items to return.
                        pass

            # Reworking to return list of (key, value)
            results = []
            for node_id, node_data in data.items():
                inputs = node_data.get('inputs', {})
                for key, value in inputs.items():
                    if key in ('type', 'device'):
                        continue
                    if is_scalar(value):
                        results.append((f"inputs.{key}", str(value)))
            
            return results

    except Exception as e:
        print(f"Error extracting metadata from {filepath}: {e}")
        return []

from threading import Lock
import time

# Global lock for synchronization to prevent race conditions
sync_lock = Lock()
last_sync_time = 0
SYNC_COOLDOWN = 2.0  # Seconds

def sync_images(db: Session):
    global last_sync_time
    
    # Non-blocking check first (optional optimization)
    if time.time() - last_sync_time < SYNC_COOLDOWN:
        return

    # Acquire lock to ensure only one thread syncs at a time
    if not sync_lock.acquire(blocking=False):
        # If locked, assume another thread is syncing and we can skip
        return
    
    try:
        # Check again after acquiring lock (double-check locking)
        if time.time() - last_sync_time < SYNC_COOLDOWN:
            return

        print("Starting sync...")
        existing_images = {img.id: img for img in db.query(models.Image).all()}
        existing_paths = {img.path: img for img in existing_images.values()}
        
        # Walk directory
        for root, dirs, files in os.walk(IMAGES_DIR):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.mp4', '.webm', '.mov')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, IMAGES_DIR)
                    
                    mtime = os.path.getmtime(full_path)
                    created_at = datetime.fromtimestamp(mtime)

                    file_hash = calculate_sha1(full_path)
                    if not file_hash:
                        continue
                    
                    image_to_process = None
                    is_new = False
                    
                    if file_hash not in existing_images:
                        # New hash found.
                        # Check if this path is already claimed by another image (content changed)
                        if rel_path in existing_paths:
                            old_img = existing_paths[rel_path]
                            # Delete the old image since the file at this path has changed content
                            db.delete(old_img)
                            # Flush to ensure the path is freed before we try to insert a new image with the same path
                            db.flush()
                            
                            if old_img.id in existing_images:
                                del existing_images[old_img.id]
                            del existing_paths[rel_path]
                        
                        # New image
                        db_image = models.Image(id=file_hash, path=rel_path, created_at=created_at)
                        db.add(db_image)
                        
                        # Update local lookups
                        existing_images[file_hash] = db_image
                        existing_paths[rel_path] = db_image
                        
                        image_to_process = db_image
                        is_new = True
                    else:
                        existing_img = existing_images[file_hash]
                        if existing_img.created_at != created_at:
                             existing_img.created_at = created_at
                             db.add(existing_img)
                        
                        if existing_img.path != rel_path:
                            # Path mismatch. 
                            # Check if old path is invalid (doesn't exist)
                            old_full_path = os.path.join(IMAGES_DIR, existing_img.path)
                            if not os.path.exists(old_full_path):
                                # The file moved from old_path to rel_path
                                
                                # Check if rel_path is free
                                if rel_path in existing_paths and existing_paths[rel_path].id != existing_img.id:
                                    # Target path is occupied by ANOTHER image.
                                    occupant = existing_paths[rel_path]
                                    db.delete(occupant)
                                    db.flush() # Flush here too
                                    if occupant.id in existing_images:
                                        del existing_images[occupant.id]
                                    del existing_paths[rel_path]

                                # Now move
                                # We must also remove the old path claim
                                if existing_img.path in existing_paths:
                                    del existing_paths[existing_img.path]
                                    
                                existing_img.path = rel_path
                                db.add(existing_img)
                                existing_paths[rel_path] = existing_img
                                
                        if not existing_img.metadata_items: 
                             image_to_process = existing_img
                    
                    if image_to_process:
                        # Extract and save metadata
                        # Only for PNGs usually, but check extension inside or let pillow handle
                        if file.lower().endswith('.png'):
                            meta_items = extract_metadata(full_path)
                            # delete existing just in case (e.g. re-processing)
                            if not is_new:
                                 db.query(models.ImageMetadata).filter(models.ImageMetadata.image_id == image_to_process.id).delete()
    
                            for k, v in meta_items:
                                db.add(models.ImageMetadata(image_id=image_to_process.id, key=k, value=v))
        
        db.commit()
        last_sync_time = time.time()
        print(f"Sync complete. Images: {len(existing_images)}")
    
    finally:
        sync_lock.release()
