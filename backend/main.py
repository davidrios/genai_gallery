import os
import hashlib
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import shutil
import re
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

import models
import schemas
import database
from database import engine, get_db
from config import IMAGES_DIR

models.Base.metadata.create_all(bind=engine)

# Create FTS5 table if not exists
with engine.connect() as connection:
    connection.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(image_id UNINDEXED, content)"))
    connection.commit()

app = FastAPI()


# Allow CORS for frontend
allowed_origins_env = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:8188")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount images directory to serve static files
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

@app.get("/api/images")
def list_images(sort: str = "desc", q: str = None, db: Session = Depends(get_db)):
    sync_images(db)
    
    query = db.query(models.Image)
    
    if q:
        # Check for exact key:value search
        if ':' in q:
            key, val = q.split(':', 1)
            query = query.join(models.ImageMetadata).filter(
                models.ImageMetadata.key == key.strip(),
                models.ImageMetadata.value.like(f"%{val.strip()}%")
            )
        else:
            # FTS Search
            # We subquery the search_index for matching IDs
            # Using raw SQL for the match
            # "SELECT image_id FROM search_index WHERE search_index MATCH :q"
            # And filter Image.id IN (...)
            
            # Sanitization for FTS5 (basic)
            safe_q = q.replace('"', '""')
            fts_sql = text("SELECT image_id FROM search_index WHERE search_index MATCH :q")
            matched_ids = [row[0] for row in db.execute(fts_sql, {"q": f'"{safe_q}"'}).fetchall()]
            
            query = query.filter(models.Image.id.in_(matched_ids))

    if sort == "asc":
        query = query.order_by(models.Image.created_at.asc())
    else:
        query = query.order_by(models.Image.created_at.desc())
        
    images = query.all()
    return images

@app.get("/api/images/{image_id}", response_model=schemas.Image)
def get_image_details(image_id: str, db: Session = Depends(get_db)):
    image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@app.get("/api/browse", response_model=schemas.BrowseResponse)
def browse(
    path: str = "", 
    sort: str = "desc", 
    q: str = None, 
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    import math
    # Security check to prevent path traversal
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # Ensure clean relative path (empty string for root)
    path = path.strip("/")
    
    full_path = os.path.join(IMAGES_DIR, path)
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
         raise HTTPException(status_code=404, detail="Directory not found")

    sync_images(db)

    # List subdirectories (only if not searching, or keep them?)
    # If searching, we probably want to search everything recursively, ignoring the current directory Browse?
    # Or search only within this directory? 
    # Logic: Search usually implies "find anywhere". 
    # If q is present, we ignore directory structure and return all matching images.
    
    directories = []
    if not q:
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

    # List images
    query = db.query(models.Image)
    
    if q:
        # Search Mode: Global Search (ignores path)
        if ':' in q:
            key, val = q.split(':', 1)
            query = query.join(models.ImageMetadata).filter(
                models.ImageMetadata.key == key.strip(),
                models.ImageMetadata.value.like(f"%{val.strip()}%")
            )
        else:
            safe_q = q.replace('"', '""')
            fts_sql = text("SELECT image_id FROM search_index WHERE search_index MATCH :q")
            matched_ids = [row[0] for row in db.execute(fts_sql, {"q": f'"{safe_q}"'}).fetchall()]
            query = query.filter(models.Image.id.in_(matched_ids))
    else:
        # Browse Mode: Filter by keys/indexes or filter in python later
        # Optimization: To avoid fetching all images, maybe we can filter by path prefix? 
        # But images stores relative path.
        pass # We will filter by directory in Python as before if no search
    
    if sort == "asc":
        query = query.order_by(models.Image.created_at.asc())
    else:
        query = query.order_by(models.Image.created_at.desc())

    all_images = query.all()
    
    results = []
    if q:
        # Return all results
        results = all_images
    else:
        # Filter by current directory
        for img in all_images:
            img_dir = os.path.dirname(img.path)
            if img_dir == path:
                results.append(img)
            
    
    # Pagination Logic
    total_count = len(results)
    total_pages = math.ceil(total_count / limit) if limit > 0 else 1
    
    start = (page - 1) * limit
    end = start + limit
    paginated_results = results[start:end]
            
    return {
        "directories": directories,
        "images": paginated_results,
        "total": total_count,
        "page": page,
        "pages": total_pages
    }

@app.get("/api/search", response_model=schemas.PaginatedImageResponse)
def search_images(
    q: str = None, 
    page: int = 1, 
    limit: int = 12, 
    sort: str = "desc", 
    db: Session = Depends(get_db)
):
    import math
    sync_images(db)
    
    query = db.query(models.Image)
    
    # 1. Apply Filtering (Same as list_images)
    if q:
        if ':' in q:
            key, val = q.split(':', 1)
            query = query.join(models.ImageMetadata).filter(
                models.ImageMetadata.key == key.strip(),
                models.ImageMetadata.value.like(f"%{val.strip()}%")
            )
        else:
            safe_q = q.replace('"', '""')
            fts_sql = text("SELECT image_id FROM search_index WHERE search_index MATCH :q")
            matched_ids = [row[0] for row in db.execute(fts_sql, {"q": f'"{safe_q}"'}).fetchall()]
            query = query.filter(models.Image.id.in_(matched_ids))

    # 2. Apply Sorting
    if sort == "asc":
        query = query.order_by(models.Image.created_at.asc())
    else:
        query = query.order_by(models.Image.created_at.desc())
        
    # 3. Pagination
    total_count = query.count()
    offset = (page - 1) * limit
    
    # Apply limit/offset
    images = query.offset(offset).limit(limit).all()
    
    total_pages = math.ceil(total_count / limit) if limit > 0 else 1
    
    return {
        "items": images,
        "total": total_count,
        "page": page,
        "size": limit,
        "pages": total_pages
    }

@app.post("/api/upload", response_model=List[schemas.Image])
async def upload_images(
    files: List[UploadFile] = File(...),
    filename_prefix: str = Form(""),
    db: Session = Depends(get_db)
):
    # 1. Validation and Path Resolution
    # Parse prefix into directory and base filename
    # Allow slashes in prefix to denote subdirectories
    prefix_path = filename_prefix.strip("/")
    
    # Security check
    if ".." in prefix_path or prefix_path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid prefix path")

    # Split into directory and base prefix
    # If prefix ends with slash, base is empty? No, traditionally prefix is "folder/myimage" -> folder, myimage
    # If just "folder/", assume base is "image"? Or just require full prefix?
    # User said: "Suppose the prefix is `prefix`... `prefix_00001.png`". 
    # "filename_prefix can contain `/`... parent folders will be created".
    # So "folder/sub/img" -> dir="folder/sub", base="img"
    
    dirname = os.path.dirname(prefix_path)
    basename = os.path.basename(prefix_path)
    
    full_dir_path = os.path.join(IMAGES_DIR, dirname)
    
    # Ensure directory exists
    os.makedirs(full_dir_path, exist_ok=True)
    
    # 2. Find next sequence number
    # We look for files matching basename_XXXXX.* in the directory
    # Regex: escaped_basename + _ + 5 digits + dot + extension
    
    # Escape basename for regex
    safe_basename = re.escape(basename)
    pattern = re.compile(rf"^{safe_basename}_(\d{{5}})\.[a-zA-Z0-9]+$")
    
    max_idx = 0
    try:
        with os.scandir(full_dir_path) as it:
            for entry in it:
                if entry.is_file():
                    match = pattern.match(entry.name)
                    if match:
                        idx = int(match.group(1))
                        if idx > max_idx:
                            max_idx = idx
    except OSError:
        pass # Directory might be new/empty if just created, or permission error (shouldn't happen with makedirs)
        
    start_idx = max_idx + 1
    created_images = []
    
    # 3. Save files
    for i, file in enumerate(files):
        current_idx = start_idx + i
        
        # Get extension from original filename
        # Fallback to .png if unknown? Or just use original?
        original_ext = os.path.splitext(file.filename)[1].lower()
        if not original_ext:
            original_ext = ".png" # Default
            
        new_filename = f"{basename}_{current_idx:05d}{original_ext}"
        save_path = os.path.join(full_dir_path, new_filename)
        
        # Save to disk
        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            print(f"Failed to save file {new_filename}: {e}")
            continue

        # 4. Add to Database
        # Calculate hash
        file_hash = calculate_sha1(save_path)
        if not file_hash:
            continue
            
        rel_path = os.path.relpath(save_path, IMAGES_DIR)
        created_at = datetime.now()
        
        # Check if hash already exists? 
        # API usually implies new content. If duplicate hash exists, we might reuse the entry or update path?
        # sync_images handles this. Let's try to mimic sync logic or just do a quick insert.
        # But we must be careful not to conflict with existing UNIQUE(path) if we somehow overwrote a file (unlikely with seq).
        # However, reusing sync_images logic for this single file is safer but extracting it is complex.
        
        # Check existing path
        existing_path_img = db.query(models.Image).filter(models.Image.path == rel_path).first()
        if existing_path_img:
            db.delete(existing_path_img)
            db.flush()
            
        # Check existing hash
        existing_img = db.query(models.Image).filter(models.Image.id == file_hash).first()
        
        img_obj = None
        is_new_meta = False
        
        if existing_img:
            # File content existed elsewhere or previously.
            # We are creating a NEW copy at `rel_path`. 
            # If `existing_img` points to a different path, we have a duplicate.
            # Our model enforces UNIQUE path, but ID is primary key.
            # ID is hash. So identical images share ID?
            # models.Image(id=Hash, path=Prop). 
            # If ID is PK, we can't have two rows with same Hash but different Path.
            # Wait, `id = Column(String, primary_key=True)`.
            # If I copy an image, the new file has same Hash.
            # Database Integrity Error if I try to insert new row with same ID!
            # So... my data model assumes UNIQUE HASH across the gallery (deduplication).
            # If `existing_img` exists, it means we already have this image at `existing_img.path`.
            # But we just saved it to `rel_path`.
            # If I want to support duplicates in FS but dedup in DB, I must update the DB to point to *one* of them?
            # Or the Model is wrong for a standard gallery where duplicates are allowed?
            # "Add to Database" implies we track it.
            # If user uploads duplicate, maybe just return existing?
            # BUT the file IS on disk at `new_filename`.
            # If the DB tracks `path`, and `id` is PK, then we can only track ONE path per hash.
            # This is a limitation of current schema. 
            # Let's assume for now we update the path to the NEW one (most recent), 
            # OR we fail silently on DB update and just return existing.
            # Let's update path to the new one as it's "freshly uploaded".
            
            existing_img.path = rel_path
            existing_img.created_at = created_at
            db.add(existing_img)
            db.commit() # Commit to save path change
            img_obj = existing_img
            # Metadata might already exist
        else:
            # New unique image
            img_obj = models.Image(id=file_hash, path=rel_path, created_at=created_at)
            db.add(img_obj)
            db.commit()
            is_new_meta = True
            
        # 5. Extract Metadata
        if is_new_meta or not img_obj.metadata_items: # re-extract if missing
             # Extract
            if save_path.lower().endswith('.png'):
                meta_items = extract_metadata(save_path)
                
                # Delete old
                db.query(models.ImageMetadata).filter(models.ImageMetadata.image_id == img_obj.id).delete()
                
                # Insert new
                new_meta_rows = []
                for k, v in meta_items:
                    new_meta_rows.append(models.ImageMetadata(image_id=img_obj.id, key=k, value=v))
                db.add_all(new_meta_rows)
                
                # Update FTS
                db.execute(text("DELETE FROM search_index WHERE image_id = :id"), {"id": img_obj.id})
                search_content = [img_obj.path, getattr(img_obj, 'prompt', '') or ""]
                search_content.extend([v for k, v in meta_items])
                full_text = " ".join(search_content)
                db.execute(text("INSERT INTO search_index (image_id, content) VALUES (:id, :content)"), 
                           {"id": img_obj.id, "content": full_text})
                
                db.commit()
                
        # Reload to get relationships
        db.refresh(img_obj)
        created_images.append(img_obj)
        
    return created_images

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
            # Reworking to return list of (key, value)
            items = []
            for node_id, node_data in data.items():
                inputs = node_data.get('inputs', {})
                for inp_key, inp_val in inputs.items():
                    if inp_key in ('type', 'device'):
                        continue
                    if is_scalar(inp_val):
                        # We flatten as inputs.<key>
                        # User requested to remove "inputs." prefix
                        # items.append((f"inputs.{inp_key}", str(inp_val)))
                        items.append((inp_key, str(inp_val)))
                    elif isinstance(inp_val, list):
                        pass # ignore arrays for now or join them?
                
            return items

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
                        
                            # Update Search Index
                            # We delete old FTS entry first
                            db.execute(text("DELETE FROM search_index WHERE image_id = :id"), {"id": image_to_process.id})
                            
                            # Aggregate content: path + prompt + all metadata values
                            search_content = [image_to_process.path, getattr(image_to_process, 'prompt', '') or ""]
                            search_content.extend([v for k, v in meta_items])
                            full_text = " ".join(search_content)
                            
                            db.execute(text("INSERT INTO search_index (image_id, content) VALUES (:id, :content)"), 
                                       {"id": image_to_process.id, "content": full_text})
        
        db.commit()
        last_sync_time = time.time()
        print(f"Sync complete. Images: {len(existing_images)}")
    
    finally:
        sync_lock.release()
