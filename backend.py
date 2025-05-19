from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from fastapi.staticfiles import StaticFiles
from PIL import Image
import numpy as np
import os
import json
from datetime import datetime, timedelta
from typing import List, Optional
# import jwt
from jose import jwt
from passlib.context import CryptContext
import uuid

from api.encrypt import encrypt_img
from api.decrypt import decrypt_img
from api.preview import generate_preview
from utils.utils import save_encrypted_array, load_encrypted_array, save_np_as_image

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve storage folder
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# Folder paths
TMP_UPLOAD = "temp_uploads"
STORAGE_ENC_ARRAY = "storage/encrypted"
STORAGE_ENC_VIEW = "storage/encrypted_view"
STORAGE_PREVIEW = "storage/preview"
STORAGE_DECRYPTED = "storage/decrypted"

# Create folders if not exist
for folder in [TMP_UPLOAD, STORAGE_ENC_ARRAY, STORAGE_ENC_VIEW, STORAGE_PREVIEW, STORAGE_DECRYPTED]:
    os.makedirs(folder, exist_ok=True)

# === Authentication Setup ===
SECRET_KEY = "your-secret-key-here"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# === API MODELS ===
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class Item(BaseModel):
    id: str
    name: str
    type: str
    preview: str
    path: str
    starred: bool = False
    last_modified: str
    parent_folder: Optional[str] = None
    user_id: str

class Folder(BaseModel):
    id: str
    name: str
    type: str = "folder"
    parent_folder: Optional[str] = None
    created_at: str
    user_id: str

# File to store metadata
METADATA_FILE = "storage/metadata.json"
IMAGE_FOLDERS_FILE = "storage/image_folders.json"

def load_metadata():
    print("Loading metadata from:", METADATA_FILE)
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                data = json.load(f)
                print("Loaded metadata:", data)
                # Ensure required fields exist
                if not isinstance(data, dict):
                    data = {}
                if "starred" not in data:
                    data["starred"] = []
                if "folders" not in data:
                    data["folders"] = []
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading metadata: {str(e)}")
    return {"starred": [], "folders": []}

def load_image_folders():
    if os.path.exists(IMAGE_FOLDERS_FILE):
        try:
            with open(IMAGE_FOLDERS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def save_image_folders(image_folders):
    os.makedirs(os.path.dirname(IMAGE_FOLDERS_FILE), exist_ok=True)
    with open(IMAGE_FOLDERS_FILE, 'w') as f:
        json.dump(image_folders, f, indent=2)

def save_metadata(metadata):
    print("Saving metadata:", metadata)
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    print("Metadata saved successfully")

# Initialize metadata if it doesn't exist or is invalid
metadata = load_metadata()
save_metadata(metadata)

# === User Management Functions ===
def get_users():
    if os.path.exists("storage/users.json"):
        with open("storage/users.json", "r") as f:
            return json.load(f)
    return {"users": []}

def save_users(users_data):
    os.makedirs("storage", exist_ok=True)
    with open("storage/users.json", "w") as f:
        json.dump(users_data, f, indent=2)

def get_user_by_email(email: str):
    users_data = get_users()
    for user in users_data["users"]:
        if user["email"] == email:
            return user
    return None

def create_user(user: UserCreate):
    users_data = get_users()
    
    # Check if user already exists
    if get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = pwd_context.hash(user.password)
    
    new_user = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "hashed_password": hashed_password,
        "created_at": datetime.now().isoformat()
    }
    
    users_data["users"].append(new_user)
    save_users(users_data)
    
    return {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "created_at": new_user["created_at"]
    }

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.JWTError:
        raise credentials_exception
    user = get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# === Authentication Endpoints ===
@app.post("/api/auth/signup", response_model=User)
async def signup(user: UserCreate):
    return create_user(user)

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# === Protected Routes ===
@app.get("/api/users/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "created_at": current_user["created_at"]
    }

# === FOLDER ENDPOINTS ===
@app.post("/api/folders")
async def create_folder(
    name: str = Form(...),
    parent_folder: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    print(f"Received folder creation request - Name: {name}, Parent: {parent_folder}")
    try:
        metadata = load_metadata()
        
        # Create folder ID (sanitized name)
        folder_id = name.replace(" ", "_").lower()
        print(f"Generated folder ID: {folder_id}")
        
        # Check if folder already exists
        if any(f["id"] == folder_id and f["user_id"] == current_user["id"] for f in metadata["folders"]):
            print(f"Folder {folder_id} already exists")
            raise HTTPException(status_code=400, detail="Folder already exists")
        
        # Create new folder
        new_folder = {
            "id": folder_id,
            "name": name,
            "type": "folder",
            "parent_folder": parent_folder,
            "created_at": datetime.now().isoformat(),
            "user_id": current_user["id"]
        }
        print(f"Created new folder object: {new_folder}")
        
        # Ensure the storage directory exists
        os.makedirs("storage", exist_ok=True)
        
        # Add to metadata
        metadata["folders"].append(new_folder)
        save_metadata(metadata)
        
        print(f"Successfully created folder: {new_folder}")
        return new_folder
    except Exception as e:
        print(f"Error creating folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")

@app.get("/api/folders")
async def list_folders(current_user: dict = Depends(get_current_user)):
    print("Received request to list folders")
    try:
        metadata = load_metadata()
        user_folders = [f for f in metadata["folders"] if f["user_id"] == current_user["id"]]
        print(f"Current folders: {user_folders}")
        return user_folders
    except Exception as e:
        print(f"Error listing folders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list folders: {str(e)}")

# === STAR/UNSTAR ENDPOINTS ===
@app.post("/api/items/{item_id}/star")
async def star_item(item_id: str):
    print(f"Attempting to star item: {item_id}")
    metadata = load_metadata()
    print(f"Current starred items: {metadata['starred']}")
    if item_id not in metadata["starred"]:
        metadata["starred"].append(item_id)
        save_metadata(metadata)
        print(f"Successfully starred item: {item_id}")
    return {"status": "success"}

@app.post("/api/items/{item_id}/unstar")
async def unstar_item(item_id: str):
    print(f"Attempting to unstar item: {item_id}")
    metadata = load_metadata()
    print(f"Current starred items: {metadata['starred']}")
    if item_id in metadata["starred"]:
        metadata["starred"].remove(item_id)
        save_metadata(metadata)
        print(f"Successfully unstarred item: {item_id}")
    return {"status": "success"}

# === MODIFIED LIST ITEMS ENDPOINT ===
@app.get("/api/items", response_model=list[Item])
def list_items(folder: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    items = []
    metadata = load_metadata()
    starred_items = metadata["starred"]
    image_folders = load_image_folders()
    user_id = current_user["id"]
    
    for fname in os.listdir(STORAGE_PREVIEW):
        if fname.endswith(".png"):
            base = os.path.splitext(fname)[0]
            original_name = base.replace("_preview", "").replace("_encrypted", "")
            
            # Get the folder assignment for this image
            current_folder = image_folders.get(base)
            
            # Skip if we're filtering by folder and this image isn't in the requested folder
            if folder is not None and current_folder != folder:
                continue
            
            item = Item(
                id=base,
                name=original_name,
                type="file",
                preview=f"/api/preview/{base}",
                path=f"/storage/preview/{fname}",
                starred=base in starred_items,
                last_modified=datetime.fromtimestamp(
                    os.path.getmtime(os.path.join(STORAGE_PREVIEW, fname))
                ).isoformat(),
                parent_folder=current_folder,
                user_id=user_id
            )
            items.append(item)
    
    items.sort(key=lambda x: x.last_modified, reverse=True)
    return items

@app.get("/api/items/starred")
def list_starred_items(current_user: dict = Depends(get_current_user)):
    metadata = load_metadata()
    all_items = list_items(current_user=current_user)
    return [item for item in all_items if item.id in metadata["starred"] and item.user_id == current_user["id"]]

@app.get("/api/items/recent")
def list_recent_items(limit: int = 5, current_user: dict = Depends(get_current_user)):
    all_items = list_items(current_user=current_user)
    # Sort by last_modified and return the most recent items for the current user
    user_items = [item for item in all_items if item.user_id == current_user["id"]]
    return sorted(user_items, key=lambda x: x.last_modified, reverse=True)[:limit]

# === PREVIEW ENDPOINT ===
@app.get("/api/preview/{item_id}")
def get_preview(item_id: str):
    path = os.path.join(STORAGE_PREVIEW, f"{item_id}.png")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Preview not found")
    return FileResponse(path, media_type="image/png")

# === DELETE ENDPOINT ===
@app.delete("/api/delete/{filename}")
async def delete_endpoint(filename: str):
    print(f"Delete request received for filename: {filename}")
    
    # The filename we receive should be the original name without suffixes
    # We need to construct the full filenames
    enc_id = f"{filename}_encrypted"
    preview_id = f"{enc_id}_preview"
    
    # List of files to delete with their full paths
    files_to_delete = [
        os.path.join(STORAGE_ENC_ARRAY, f"{enc_id}.npy"),
        os.path.join(STORAGE_ENC_VIEW, f"{enc_id}.tiff"),
        os.path.join(STORAGE_PREVIEW, f"{preview_id}.png")
    ]
    
    print(f"Attempting to delete files: {files_to_delete}")
    
    # Try to delete each file
    deleted_files = []
    for file_path in files_to_delete:
        try:
            print(f"Checking file: {file_path}")
            if os.path.exists(file_path):
                print(f"File exists, deleting: {file_path}")
                os.remove(file_path)
                deleted_files.append(os.path.basename(file_path))
            else:
                print(f"File does not exist: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {str(e)}")
    
    if not deleted_files:
        print(f"No files were deleted for filename: {filename}")
        raise HTTPException(
            status_code=404, 
            detail=f"No files found to delete. Checked paths: {[os.path.basename(f) for f in files_to_delete]}"
        )
    
    print(f"Successfully deleted files: {deleted_files}")
    return JSONResponse(content={
        "message": "Files deleted successfully",
        "deleted_files": deleted_files,
        "original_filename": filename
    })

# === ENCRYPTION ===
@app.post("/api/encrypt", response_class=JSONResponse)
async def encrypt_endpoint(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    temp_path = os.path.join(TMP_UPLOAD, file.filename)
    contents = await file.read()
    with open(temp_path, "wb") as f:
        f.write(contents)

    image = Image.open(temp_path)
    array = np.array(image)

    encrypted_array, key = encrypt_img(array)
    base = os.path.splitext(file.filename)[0]
    enc_id = f"{base}_encrypted"

    npy_path = os.path.join(STORAGE_ENC_ARRAY, f"{enc_id}.npy")
    enc_view_path = os.path.join(STORAGE_ENC_VIEW, f"{enc_id}.tiff")
    preview_path = os.path.join(STORAGE_PREVIEW, f"{enc_id}_preview.png")

    save_encrypted_array(encrypted_array, npy_path)
    save_np_as_image(encrypted_array, enc_view_path)
    save_np_as_image(generate_preview(array), preview_path,mode='PNG')

    return {
        "message": "✅ Encryption successful",
        "encryption_key": str(key),
        "preview_id": f"{enc_id}_preview",
        "encrypted_id": enc_id,
        "preview_image_path": f"/storage/preview/{enc_id}_preview.png",
        "user_id": current_user["id"]
    }

# === DECRYPTION ===
@app.post("/api/decrypt")
async def decrypt_endpoint(filename: str = Form(...), key: str = Form(...)):
    base = os.path.splitext(filename)[0]
    enc_id = f"{base}_encrypted"
    npy_path = os.path.join(STORAGE_ENC_ARRAY, f"{enc_id}.npy")

    if not os.path.exists(npy_path):
        raise HTTPException(status_code=404, detail="Encrypted file not found")

    try:
        key_tuple = tuple(map(float, key.strip("()").split(",")))
        if len(key_tuple) != 5:
            raise ValueError()
    except:
        raise HTTPException(status_code=400, detail="Invalid key format")

    encrypted_array = load_encrypted_array(npy_path)
    decrypted = decrypt_img(encrypted_array, key_tuple)

    dec_path = os.path.join(STORAGE_DECRYPTED, f"{base}_decrypted.tiff")
    save_np_as_image(decrypted, dec_path)

    return FileResponse(dec_path, media_type="image/tiff", filename=os.path.basename(dec_path))

# Add endpoint to move image to folder
@app.post("/api/items/{item_id}/move")
async def move_item(item_id: str, folder_id: Optional[str] = Form(None)):
    print(f"Moving item {item_id} to folder {folder_id}")
    
    # Load the image-folder relationships
    image_folders = load_image_folders()
    
    # Update the folder assignment
    if folder_id:
        # Verify folder exists
        metadata = load_metadata()
        if not any(f["id"] == folder_id for f in metadata["folders"]):
            raise HTTPException(status_code=404, detail="Folder not found")
        image_folders[item_id] = folder_id
    else:
        # If folder_id is None, remove the image from its current folder
        image_folders.pop(item_id, None)
    
    # Save the updated relationships
    save_image_folders(image_folders)
    
    return {"status": "success"}

@app.get("/api/search")
def search_items(query: str, folder: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    print(f"Searching for '{query}' in folder: {folder}")
    items = []
    metadata = load_metadata()
    starred_items = metadata["starred"]
    image_folders = load_image_folders()
    user_id = current_user["id"]
    
    for fname in os.listdir(STORAGE_PREVIEW):
        if fname.endswith(".png"):
            base = os.path.splitext(fname)[0]
            original_name = base.replace("_preview", "").replace("_encrypted", "")
            
            # Get the folder assignment for this image
            current_folder = image_folders.get(base)
            
            # Skip if we're filtering by folder and this image isn't in the requested folder
            if folder is not None and current_folder != folder:
                continue
            
            # Check if the search query matches the filename
            if query.lower() in original_name.lower():
                item = Item(
                    id=base,
                    name=original_name,
                    type="file",
                    preview=f"/api/preview/{base}",
                    path=f"/storage/preview/{fname}",
                    starred=base in starred_items,
                    last_modified=datetime.fromtimestamp(
                        os.path.getmtime(os.path.join(STORAGE_PREVIEW, fname))
                    ).isoformat(),
                    parent_folder=current_folder,
                    user_id=user_id
                )
                items.append(item)
    
    items.sort(key=lambda x: x.last_modified, reverse=True)
    return items
