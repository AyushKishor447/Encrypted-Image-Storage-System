from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Body
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
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
# this is a change to test workflow dadadhkhkadaadasewewasnjjjjeeqeqeqeq
from api.encrypt import encrypt_img
from api.decrypt import decrypt_img
from api.preview import generate_preview
from utils.utils import save_encrypted_array, load_encrypted_array, save_np_as_image
load_dotenv()
app = FastAPI()

# Get allowed origins from environment variable, default to localhost
allowed_origins_str = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://16.170.254.53:3000,encrypted-image-storage-system.vercel.app")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get absolute paths for storage directories
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
STORAGE_ENC_VIEW_DIR = os.path.join(STORAGE_DIR, "encrypted_view")
STORAGE_PREVIEW_DIR = os.path.join(STORAGE_DIR, "preview")
STORAGE_DECRYPTED_DIR = os.path.join(STORAGE_DIR, "decrypted")

# Serve storage folders
# app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage") # Commented out

# Folder paths
TMP_UPLOAD = os.path.join(BASE_DIR, "temp_uploads")
STORAGE_ENC_ARRAY = os.path.join(STORAGE_DIR, "encrypted")
STORAGE_ENC_VIEW = STORAGE_ENC_VIEW_DIR
STORAGE_PREVIEW = STORAGE_PREVIEW_DIR
STORAGE_DECRYPTED = STORAGE_DECRYPTED_DIR

# Create folders if not exist
for folder in [TMP_UPLOAD, STORAGE_ENC_ARRAY, STORAGE_ENC_VIEW, STORAGE_PREVIEW, STORAGE_DECRYPTED]:
    os.makedirs(folder, exist_ok=True)

# === Authentication Setup ===
SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Change this in production!
# SECRET_KEY = "KsJUuzzzU7ZK0YeGognCcznGzEVjhe2wgkVtnp1eBkug+Cz3dfpQW8R8bvjtaVJtKq4pQqnef1zqxmsxd9w12g=="  # Change this in production!
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
# METADATA_FILE = "storage/metadata.json"
# IMAGE_FOLDERS_FILE = "storage/image_folders.json"

# def load_metadata():
#     print("Loading metadata from:", METADATA_FILE)
#     if os.path.exists(METADATA_FILE):
#         try:
#             with open(METADATA_FILE, 'r') as f:
#                 data = json.load(f)
#                 print("Loaded metadata:", data)
#                 # Ensure required fields exist
#                 if not isinstance(data, dict):
#                     data = {}
#                 if "starred" not in data:
#                     data["starred"] = []
#                 if "folders" not in data:
#                     data["folders"] = []
#                 return data
#         except (json.JSONDecodeError, IOError) as e:
#             print(f"Error loading metadata: {str(e)}")
#     return {"starred": [], "folders": []}

# def load_image_folders():
#     if os.path.exists(IMAGE_FOLDERS_FILE):
#         try:
#             with open(IMAGE_FOLDERS_FILE, 'r') as f:
#                 return json.load(f)
#         except (json.JSONDecodeError, IOError):
#             pass
#     return {}

# def save_image_folders(image_folders):
#     os.makedirs(os.path.dirname(IMAGE_FOLDERS_FILE), exist_ok=True)
#     with open(IMAGE_FOLDERS_FILE, 'w') as f:
#         json.dump(image_folders, f, indent=2)

# def save_metadata(metadata):
#     print("Saving metadata:", metadata)
#     os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
#     with open(METADATA_FILE, 'w') as f:
#         json.dump(metadata, f, indent=2)
#     print("Metadata saved successfully")

# Initialize metadata if it doesn't exist or is invalid
# metadata = load_metadata()
# save_metadata(metadata)

# === User Management Functions ===

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=True,
    serverSelectionTimeoutMS=5000,
    retryWrites=True,
    retryReads=True,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    waitQueueTimeoutMS=5000
)
db = client["ess_database"]  # Use your actual DB name
# db = client["ESS-DATABASE"]  # Use your actual DB name

def get_user_by_email(email: str):
    user = db.users.find_one({"email": email})
    return user

def create_user(user: UserCreate):
    # Check if user already exists
    if get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    hashed_password = pwd_context.hash(user.password)
    new_user = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "hashed_password": hashed_password,
        "created_at": datetime.now().isoformat()
    }
    db.users.insert_one(new_user)
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
        folder_id = name.replace(" ", "_").lower()
        print(f"Generated folder ID: {folder_id}")
        # Check if folder already exists
        if db.folders.find_one({"id": folder_id, "user_id": current_user["id"]}):
            print(f"Folder {folder_id} already exists")
            raise HTTPException(status_code=400, detail="Folder already exists")
        new_folder = {
            "id": folder_id,
            "name": name,
            "type": "folder",
            "parent_folder": parent_folder,
            "created_at": datetime.now().isoformat(),
            "user_id": current_user["id"]
        }
        db.folders.insert_one(new_folder)
        if "_id" in new_folder:
            del new_folder["_id"]
        print(f"Successfully created folder: {new_folder}")
        return new_folder
    except Exception as e:
        print(f"Error creating folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")

@app.get("/api/folders")
async def list_folders(current_user: dict = Depends(get_current_user)):
    print("Received request to list folders")
    try:
        user_folders = list(db.folders.find({"user_id": current_user["id"]}, {"_id": 0}))
        print(f"Current folders: {user_folders}")
        return user_folders
    except Exception as e:
        print(f"Error listing folders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list folders: {str(e)}")

@app.delete("/api/folders/{folder_id}")
async def delete_folder(folder_id: str, current_user: dict = Depends(get_current_user)):
    # Find the folder
    folder = db.folders.find_one({"id": folder_id, "user_id": current_user["id"]})
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    # Find all images in this folder
    images_in_folder = list(db.images.find({"parent_folder": folder_id, "user_id": current_user["id"]}))
    # Delete all images in this folder
    for image in images_in_folder:
        db.images.delete_one({"id": image["id"], "user_id": current_user["id"]})
        # Optionally: delete files from disk as well (not shown here)
    # Delete the folder
    db.folders.delete_one({"id": folder_id, "user_id": current_user["id"]})
    return {"status": "success", "deleted_images": [img["id"] for img in images_in_folder], "deleted_folder": folder_id}

# === ENCRYPTION ===
@app.post("/api/encrypt", response_class=JSONResponse)
async def encrypt_endpoint(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    print(f"Starting encryption for file: {file.filename}")
    temp_path = os.path.join(TMP_UPLOAD, file.filename)
    contents = await file.read()
    with open(temp_path, "wb") as f:
        f.write(contents)
    print(f"Saved temporary file to: {temp_path}")

    image = Image.open(temp_path)
    array = np.array(image)
    print(f"Loaded image array with shape: {array.shape}")

    encrypted_array, key = encrypt_img(array)
    base = os.path.splitext(file.filename)[0]
    enc_id = f"{base}_encrypted"

    npy_path = os.path.join(STORAGE_ENC_ARRAY, f"{enc_id}.npy")
    enc_view_path = os.path.join(STORAGE_ENC_VIEW, f"{enc_id}.tiff")
    preview_path = os.path.join(STORAGE_PREVIEW, f"{enc_id}_preview.png")

    print(f"Saving files to:")
    print(f"- NPY: {npy_path}")
    print(f"- Encrypted view: {enc_view_path}")
    print(f"- Preview: {preview_path}")

    save_encrypted_array(encrypted_array, npy_path)
    save_np_as_image(encrypted_array, enc_view_path)
    save_np_as_image(generate_preview(array), preview_path, mode='PNG')

    # Verify files were created
    for path in [npy_path, enc_view_path, preview_path]:
        if os.path.exists(path):
            print(f"✅ File exists: {path}")
        else:
            print(f"❌ File missing: {path}")

    # Insert image metadata into MongoDB
    image_doc = {
        "id": f"{enc_id}_preview",
        "name": file.filename,
        "type": "file",
        "preview": f"/api/preview/{enc_id}_preview",
        "path": f"/storage/preview/{enc_id}_preview.png",
        "encrypted_path": f"/storage/encrypted_view/{enc_id}.tiff",
        "starred": False,
        "last_modified": datetime.now().isoformat(),
        "parent_folder": None,
        "user_id": current_user["id"]
    }
    db.images.insert_one(image_doc)
    print(f"✅ Saved image metadata to MongoDB: {image_doc}")

    return {
        "message": "✅ Encryption successful",
        "encryption_key": str(key),
        "preview_id": f"{enc_id}_preview",
        "encrypted_id": enc_id,
        "preview_image_path": f"/storage/preview/{enc_id}_preview.png",
        "encrypted_file_path": f"/storage/encrypted_view/{enc_id}.tiff",
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

# === MODIFIED LIST ITEMS ENDPOINT ===
@app.get("/api/items", response_model=list[Item])
def list_items(
    folder: Optional[str] = None,
    shared: Optional[bool] = False,
    current_user: dict = Depends(get_current_user)
):
    if shared:
        # Find all image_ids shared with this user
        shared_records = list(db.shared_images.find({"shared_with_email": current_user["email"]}))
        if not shared_records:
            return []  # No shared images, return empty list
        shared_image_ids = [rec["image_id"] for rec in shared_records]
        query = {"id": {"$in": shared_image_ids}}
        if folder is not None:
            query["parent_folder"] = folder
        items = list(db.images.find(query, {"_id": 0}))
    else:
        query = {"user_id": current_user["id"]}
        if folder is not None:
            query["parent_folder"] = folder
        items = list(db.images.find(query, {"_id": 0}))
    items.sort(key=lambda x: x["last_modified"], reverse=True)
    return items

@app.get("/api/items/starred")
def list_starred_items(current_user: dict = Depends(get_current_user)):
    items = list(db.images.find({"user_id": current_user["id"], "starred": True}, {"_id": 0}))
    items.sort(key=lambda x: x["last_modified"], reverse=True)
    return items

@app.get("/api/items/recent")
def list_recent_items(limit: int = 5, current_user: dict = Depends(get_current_user)):
    items = list(db.images.find({"user_id": current_user["id"]}, {"_id": 0}))
    items.sort(key=lambda x: x["last_modified"], reverse=True)
    return items[:limit]

@app.post("/api/items/{item_id}/star")
async def star_item(item_id: str, current_user: dict = Depends(get_current_user)):
    result = db.images.update_one({"id": item_id, "user_id": current_user["id"]}, {"$set": {"starred": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"status": "success"}

@app.post("/api/items/{item_id}/unstar")
async def unstar_item(item_id: str, current_user: dict = Depends(get_current_user)):
    result = db.images.update_one({"id": item_id, "user_id": current_user["id"]}, {"$set": {"starred": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"status": "success"}

@app.post("/api/items/{item_id}/move")
async def move_item(item_id: str, folder_id: Optional[str] = Form(None), current_user: dict = Depends(get_current_user)):
    update = {"parent_folder": folder_id} if folder_id else {"parent_folder": None}
    result = db.images.update_one({"id": item_id, "user_id": current_user["id"]}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"status": "success"}

@app.get("/api/search")
def search_items(query: str, folder: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    search_query = {"user_id": current_user["id"], "name": {"$regex": query, "$options": "i"}}
    if folder is not None:
        search_query["parent_folder"] = folder
    items = list(db.images.find(search_query, {"_id": 0}))
    items.sort(key=lambda x: x["last_modified"], reverse=True)
    return items

# === PREVIEW ENDPOINT ===
@app.get("/api/preview/{item_id}")
def get_preview(item_id: str):
    path = os.path.join(STORAGE_PREVIEW, f"{item_id}.png")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Preview not found")
    return FileResponse(path, media_type="image/png")

# === ENCRYPTED FILE ENDPOINT ===
@app.get("/api/encrypted/{item_id}")
async def get_encrypted_file(item_id: str, current_user: dict = Depends(get_current_user)):
    try:
        print(f"Looking for image with ID: {item_id}")
        # Find the image document in MongoDB
        image_doc = db.images.find_one({"id": item_id, "user_id": current_user["id"]})
        if not image_doc:
            print(f"Image not found in database: {item_id}")
            raise HTTPException(status_code=404, detail="Image not found in database")
        
        # Get the encrypted file path from the document
        if "encrypted_path" not in image_doc:
            print(f"Image document missing encrypted_path: {image_doc}")
            raise HTTPException(status_code=404, detail="Image document missing encrypted path")
        
        # Convert the stored path to a filesystem path
        enc_path = os.path.join(BASE_DIR, image_doc["encrypted_path"].lstrip('/'))
        print(f"Looking for encrypted file at: {enc_path}")
        
        if not os.path.exists(enc_path):
            print(f"File not found at path: {enc_path}")
            raise HTTPException(status_code=404, detail="Encrypted file not found on disk")
        
        print(f"Found encrypted file, sending response")
        return FileResponse(
            enc_path,
            media_type="image/tiff",
            filename=os.path.basename(enc_path),
            headers={"Content-Disposition": f"attachment; filename={os.path.basename(enc_path)}"}
        )
    except Exception as e:
        print(f"Error serving encrypted file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving encrypted file: {str(e)}")

# === DELETE ENDPOINT ===
@app.delete("/api/delete/{image_id}")
async def delete_endpoint(image_id: str, current_user: dict = Depends(get_current_user)):
    # Find the image document in MongoDB
    image_doc = db.images.find_one({"id": image_id, "user_id": current_user["id"]})
    if not image_doc:
        raise HTTPException(status_code=404, detail="Image not found in database")

    # Build the file paths from the document
    base = image_doc["id"].replace("_preview", "")
    npy_path = os.path.join(STORAGE_ENC_ARRAY, f"{base}.npy")
    enc_view_path = os.path.join(STORAGE_ENC_VIEW, f"{base}.tiff")
    preview_path = os.path.join(STORAGE_PREVIEW, f"{image_doc['id']}.png")

    files_to_delete = [npy_path, enc_view_path, preview_path]
    deleted_files = []
    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(os.path.basename(file_path))
        except Exception as e:
            print(f"Error deleting {file_path}: {str(e)}")

    # Remove the image document from MongoDB
    db.images.delete_one({"id": image_id, "user_id": current_user["id"]})

    if not deleted_files:
        raise HTTPException(
            status_code=404,
            detail=f"No files found to delete. Checked paths: {[os.path.basename(f) for f in files_to_delete]}"
        )

    return JSONResponse(content={
        "message": "Files deleted successfully",
        "deleted_files": deleted_files,
        "image_id": image_id
    })

@app.post("/api/decrypt-upload")
async def decrypt_upload_endpoint(file: UploadFile = File(...), key: str = Form(...)):
    # Read the uploaded file and convert to numpy array
    contents = await file.read()
    import tempfile
    import numpy as np
    from PIL import Image
    with tempfile.NamedTemporaryFile(delete=False, suffix='.tiff') as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    image = Image.open(tmp_path)
    encrypted_array = np.array(image)
    # Parse the key
    try:
        key_tuple = tuple(map(float, key.strip("() ").split(",")))
        if len(key_tuple) != 5:
            raise ValueError()
    except:
        raise HTTPException(status_code=400, detail="Invalid key format")
    # Decrypt
    decrypted = decrypt_img(encrypted_array, key_tuple)
    dec_path = tmp_path.replace('.tiff', '_decrypted.tiff')
    save_np_as_image(decrypted, dec_path)
    return FileResponse(dec_path, media_type="image/tiff", filename="decrypted_result.tiff")

@app.post("/api/share")
async def share_images(
    data: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    image_ids = data.get("image_ids")
    email = data.get("email")
    if not image_ids or not isinstance(image_ids, list) or not email:
        raise HTTPException(status_code=400, detail="Missing image_ids or email")
    # Only allow sharing images the user owns
    for image_id in image_ids:
        image = db.images.find_one({"id": image_id, "user_id": current_user["id"]})
        if not image:
            raise HTTPException(status_code=403, detail=f"You do not own image {image_id}")
        # Prevent duplicate shares
        if not db.shared_images.find_one({"image_id": image_id, "shared_with_email": email}):
            db.shared_images.insert_one({"image_id": image_id, "shared_with_email": email})
    return {"status": "success", "shared": len(image_ids), "email": email}
