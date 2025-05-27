import os
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from datetime import datetime, timedelta
import uuid
import shutil
import time
from typing import Optional
from api.encrypt import encrypt_img
from api.decrypt import decrypt_img
from api.preview import generate_preview
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a minimal FastAPI app for testing
app = FastAPI()

# Test configuration
TEST_DIR = "test_storage"
TEST_ENC_DIR = os.path.join(TEST_DIR, "encrypted")
TEST_PREVIEW_DIR = os.path.join(TEST_DIR, "preview")
TEST_DEC_DIR = os.path.join(TEST_DIR, "decrypted")

# Test user configuration from environment variables
TEST_EMAIL = os.getenv("TEST_USER_EMAIL", "testuser@example.com")
TEST_PASSWORD = os.getenv("TEST_USER_PASSWORD", "testpassword123")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
print(f"Using MongoDB URI: {MONGO_URI}")
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=True,
    serverSelectionTimeoutMS=30000,
    retryWrites=True,
    retryReads=True,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    waitQueueTimeoutMS=5000,
    connectTimeoutMS=30000,
    socketTimeoutMS=30000,
    ssl_cert_reqs='CERT_NONE'
)
db = client["ess_database"]

# Add error handling for MongoDB connection
try:
    # Verify connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {str(e)}")
    # Don't raise the error immediately, allow tests to continue
    print("Continuing with tests despite MongoDB connection error...")

# Security setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None or email != TEST_EMAIL:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"email": email, "id": "test_user_id"}
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Helper function to save numpy array as image
def save_np_as_image(array, path, mode='TIFF'):
    img = Image.fromarray(array.astype(np.uint8))
    img.save(path)

# Helper function to save encrypted array
def save_encrypted_array(array, path):
    np.save(path, array)

# Helper function to load encrypted array
def load_encrypted_array(path):
    return np.load(path)

def ensure_test_directories():
    """Ensure all test directories exist"""
    print("\nSetting up test directories:")
    for dir_path in [TEST_DIR, TEST_ENC_DIR, TEST_PREVIEW_DIR, TEST_DEC_DIR]:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Directory exists: {dir_path}")
        print(f"   Contents: {os.listdir(dir_path)}")

# Test endpoints
@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != TEST_EMAIL or form_data.password != TEST_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/encrypt", response_class=JSONResponse)
async def encrypt_endpoint(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    ensure_test_directories()  # Ensure directories exist
    
    # Save uploaded file temporarily
    temp_path = os.path.join(TEST_DIR, file.filename)
    contents = await file.read()
    with open(temp_path, "wb") as f:
        f.write(contents)
    
    try:
        # Process image
        image = Image.open(temp_path)
        array = np.array(image)
        image.close()  # Explicitly close the image
        
        # Encrypt using actual encryption function
        encrypted_array, key = encrypt_img(array)
        
        # Generate unique ID
        base = os.path.splitext(file.filename)[0]
        enc_id = f"{base}_encrypted"
        
        # Save files
        npy_path = os.path.join(TEST_ENC_DIR, f"{enc_id}.npy")
        enc_view_path = os.path.join(TEST_ENC_DIR, f"{enc_id}.tiff")
        preview_path = os.path.join(TEST_PREVIEW_DIR, f"{enc_id}_preview.png")
        
        print(f"Saving encrypted files:")
        print(f"- NPY path: {npy_path}")
        print(f"- Encrypted view path: {enc_view_path}")
        print(f"- Preview path: {preview_path}")
        
        save_encrypted_array(encrypted_array, npy_path)
        save_np_as_image(encrypted_array, enc_view_path)
        save_np_as_image(generate_preview(array), preview_path, mode='PNG')
        
        # Verify files were created
        for path in [npy_path, enc_view_path, preview_path]:
            if os.path.exists(path):
                print(f"✅ File exists: {path}")
            else:
                print(f"❌ File missing: {path}")
        
        # Save to MongoDB
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
            "message": "Encryption successful",
            "encryption_key": str(key),
            "preview_id": f"{enc_id}_preview",
            "encrypted_id": enc_id,
            "preview_image_path": f"/storage/preview/{enc_id}_preview.png",
            "encrypted_file_path": f"/storage/encrypted_view/{enc_id}.tiff",
            "npy_path": npy_path
        }
    finally:
        # Clean up temp file with retry mechanism
        max_retries = 3
        for i in range(max_retries):
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                break
            except PermissionError:
                if i < max_retries - 1:
                    time.sleep(0.5)  # Wait before retrying
                else:
                    raise

@app.post("/api/decrypt")
async def decrypt_endpoint(
    filename: str = Form(...),
    key: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    ensure_test_directories()  # Ensure directories exist
    
    # Use the same path construction as encryption
    base = os.path.splitext(filename)[0]
    # Remove _encrypted suffix if it exists to prevent double suffix
    if base.endswith('_encrypted'):
        base = base[:-10]  # Remove '_encrypted' suffix
    enc_id = f"{base}_encrypted"
    npy_path = os.path.join(TEST_ENC_DIR, f"{enc_id}.npy")
    
    print(f"\nDecryption process:")
    print(f"Base filename: {base}")
    print(f"Encrypted ID: {enc_id}")
    print(f"Looking for encrypted file at: {npy_path}")
    print(f"Directory contents: {os.listdir(TEST_ENC_DIR)}")
    
    if not os.path.exists(npy_path):
        print(f"File not found at path: {npy_path}")
        raise HTTPException(status_code=404, detail="Encrypted file not found")
    
    try:
        key_tuple = tuple(map(float, key.strip("()").split(",")))
        if len(key_tuple) != 5:
            raise ValueError()
    except:
        raise HTTPException(status_code=400, detail="Invalid key format")
    
    print(f"Loading encrypted array from: {npy_path}")
    encrypted_array = load_encrypted_array(npy_path)
    print(f"Decrypting with key: {key_tuple}")
    decrypted = decrypt_img(encrypted_array, key_tuple)
    
    # Use the same path format as the test expects
    dec_path = os.path.join(TEST_DEC_DIR, f"{enc_id}_decrypted.tiff")
    print(f"Saving decrypted file to: {dec_path}")
    save_np_as_image(decrypted, dec_path)
    
    if not os.path.exists(dec_path):
        print(f"Failed to save decrypted file at: {dec_path}")
        raise HTTPException(status_code=500, detail="Failed to save decrypted file")
    
    print(f"Successfully saved decrypted file at: {dec_path}")
    return FileResponse(dec_path, media_type="image/tiff", filename=os.path.basename(dec_path))

# Test client
client = TestClient(app)

# Test data
TEST_IMAGE_PATH = "test_image.tif"
ENCRYPTION_KEY = None
ENCRYPTED_FILE_NAME = None
ACCESS_TOKEN = None

def setup_test_image():
    """Create a test image if it doesn't exist"""
    if not os.path.exists(TEST_IMAGE_PATH):
        # Create a simple test image (grayscale)
        array = np.zeros((100, 100), dtype=np.uint8)
        array[25:75, 25:75] = 255  # White square in center
        save_np_as_image(array, TEST_IMAGE_PATH)

def cleanup():
    """Clean up test files with retry mechanism"""
    def remove_with_retry(path, is_dir=False):
        max_retries = 3
        for i in range(max_retries):
            try:
                if is_dir:
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                break
            except PermissionError:
                if i < max_retries - 1:
                    time.sleep(0.5)  # Wait before retrying
                else:
                    print(f"Warning: Could not remove {path}")

    # Remove test storage directory but keep test_image.tif
    if os.path.exists(TEST_DIR):
        remove_with_retry(TEST_DIR, is_dir=True)
    
    # Clean up MongoDB test data
    db.images.delete_many({"user_id": "test_user_id"})

@pytest.fixture(autouse=True)
def setup_and_cleanup():
    """Setup before each test and cleanup after"""
    print("\n=== Test Setup ===")
    ensure_test_directories()  # Ensure directories exist before each test
    setup_test_image()  # This will only create the image if it doesn't exist
    yield
    print("\n=== Test Cleanup ===")
    time.sleep(0.5)  # Add small delay before cleanup
    cleanup()

@pytest.fixture(autouse=True)
def setup_auth():
    """Setup authentication"""
    global ACCESS_TOKEN
    
    # Login to get access token
    response = client.post(
        "/api/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    ACCESS_TOKEN = response.json()["access_token"]

def test_encryption_and_decryption():
    """Test both encryption and decryption in sequence"""
    global ENCRYPTION_KEY, ENCRYPTED_FILE_NAME
    
    print("\n=== Running Encryption Test ===")
    print(f"Test image path: {TEST_IMAGE_PATH}")
    print(f"Test image exists: {os.path.exists(TEST_IMAGE_PATH)}")
    
    # Step 1: Encryption
    with open(TEST_IMAGE_PATH, "rb") as f:
        response = client.post(
            "/api/encrypt",
            files={"file": ("test_image.tif", f, "image/TIFF")},
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    print(f"Encryption response: {data}")
    
    # Store values for decryption
    ENCRYPTION_KEY = data["encryption_key"]
    ENCRYPTED_FILE_NAME = data["encrypted_id"]
    
    # Verify files were created
    npy_path = os.path.join(TEST_ENC_DIR, f"{ENCRYPTED_FILE_NAME}.npy")
    enc_view_path = os.path.join(TEST_ENC_DIR, f"{ENCRYPTED_FILE_NAME}.tiff")
    preview_path = os.path.join(TEST_PREVIEW_DIR, f"{ENCRYPTED_FILE_NAME}_preview.png")
    
    print("\nVerifying created files:")
    print(f"NPY path: {npy_path}")
    print(f"Encrypted view path: {enc_view_path}")
    print(f"Preview path: {preview_path}")
    
    assert os.path.exists(npy_path), f"NPY file not found at {npy_path}"
    assert os.path.exists(enc_view_path), f"Encrypted view file not found at {enc_view_path}"
    assert os.path.exists(preview_path), f"Preview file not found at {preview_path}"
    
    # Verify MongoDB entry
    image_doc = db.images.find_one({"id": f"{ENCRYPTED_FILE_NAME}_preview"})
    assert image_doc is not None, "Image document not found in MongoDB"
    print(f"\nMongoDB document: {image_doc}")
    
    # Step 2: Decryption
    print("\n=== Running Decryption Test ===")
    print(f"Testing decryption with:")
    print(f"ENCRYPTED_FILE_NAME: {ENCRYPTED_FILE_NAME}")
    print(f"ENCRYPTION_KEY: {ENCRYPTION_KEY}")
    print(f"TEST_ENC_DIR contents: {os.listdir(TEST_ENC_DIR)}")
    
    response = client.post(
        "/api/decrypt",
        data={"filename": ENCRYPTED_FILE_NAME, "key": ENCRYPTION_KEY},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
    )
    
    assert response.status_code == 200, f"Decryption failed with status {response.status_code}"
    assert response.headers["content-type"] == "image/tiff"
    
    # Verify decrypted file was created
    dec_path = os.path.join(TEST_DEC_DIR, f"{ENCRYPTED_FILE_NAME}_decrypted.tiff")
    print(f"\nLooking for decrypted file at: {dec_path}")
    print(f"Decrypted directory contents: {os.listdir(TEST_DEC_DIR)}")
    assert os.path.exists(dec_path), f"Decrypted file not found at {dec_path}"
    
    # Verify decrypted image can be opened
    decrypted_image = Image.open(dec_path)
    assert decrypted_image is not None
    decrypted_image.close()  # Close the image after verification 