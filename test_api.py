import os
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
import uuid
import shutil
from datetime import datetime

# Create a minimal FastAPI app for testing
app = FastAPI()

# Test configuration
TEST_DIR = "test_storage"
TEST_ENC_DIR = os.path.join(TEST_DIR, "encrypted")
TEST_PREVIEW_DIR = os.path.join(TEST_DIR, "preview")
TEST_DEC_DIR = os.path.join(TEST_DIR, "decrypted")

# Create test directories
os.makedirs(TEST_DIR, exist_ok=True)
os.makedirs(TEST_ENC_DIR, exist_ok=True)
os.makedirs(TEST_PREVIEW_DIR, exist_ok=True)
os.makedirs(TEST_DEC_DIR, exist_ok=True)

# Mock encryption function
def mock_encrypt_img(array):
    # Simple mock encryption - just add 1 to each pixel
    encrypted = array + 1
    key = (1.0, 2.0, 3.0, 4.0, 5.0)  # Mock encryption key
    return encrypted, key

# Mock decryption function
def mock_decrypt_img(encrypted_array, key):
    # Simple mock decryption - subtract 1 from each pixel
    return encrypted_array - 1

# Mock preview generation
def mock_generate_preview(array):
    # Just return the array as is for preview
    return array

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

# Test endpoints
@app.post("/api/encrypt", response_class=JSONResponse)
async def encrypt_endpoint(file: UploadFile = File(...)):
    # Save uploaded file temporarily
    temp_path = os.path.join(TEST_DIR, file.filename)
    contents = await file.read()
    with open(temp_path, "wb") as f:
        f.write(contents)

    # Process image
    image = Image.open(temp_path)
    array = np.array(image)
    
    # Encrypt
    encrypted_array, key = mock_encrypt_img(array)
    
    # Generate unique ID
    base = os.path.splitext(file.filename)[0]
    enc_id = f"{base}_encrypted"
    
    # Save files
    npy_path = os.path.join(TEST_ENC_DIR, f"{enc_id}.npy")
    enc_view_path = os.path.join(TEST_ENC_DIR, f"{enc_id}.tiff")
    preview_path = os.path.join(TEST_PREVIEW_DIR, f"{enc_id}_preview.png")
    
    save_encrypted_array(encrypted_array, npy_path)
    save_np_as_image(encrypted_array, enc_view_path)
    save_np_as_image(mock_generate_preview(array), preview_path, mode='PNG')
    
    # Clean up temp file
    os.remove(temp_path)
    
    return {
        "message": "Encryption successful",
        "encryption_key": str(key),
        "preview_id": f"{enc_id}_preview",
        "encrypted_id": enc_id,
        "preview_image_path": f"/storage/preview/{enc_id}_preview.png",
        "encrypted_file_path": f"/storage/encrypted_view/{enc_id}.tiff"
    }

@app.post("/api/decrypt")
async def decrypt_endpoint(filename: str = Form(...), key: str = Form(...)):
    base = os.path.splitext(filename)[0]
    enc_id = f"{base}_encrypted"
    npy_path = os.path.join(TEST_ENC_DIR, f"{enc_id}.npy")
    
    if not os.path.exists(npy_path):
        raise Exception("Encrypted file not found")
    
    try:
        key_tuple = tuple(map(float, key.strip("()").split(",")))
        if len(key_tuple) != 5:
            raise ValueError()
    except:
        raise Exception("Invalid key format")
    
    encrypted_array = load_encrypted_array(npy_path)
    decrypted = mock_decrypt_img(encrypted_array, key_tuple)
    
    dec_path = os.path.join(TEST_DEC_DIR, f"{base}_decrypted.tiff")
    save_np_as_image(decrypted, dec_path)
    
    return FileResponse(dec_path, media_type="image/tiff", filename=os.path.basename(dec_path))

# Test client
client = TestClient(app)

# Test data
TEST_IMAGE_PATH = "test_image.tiff"
ENCRYPTION_KEY = None
ENCRYPTED_FILE_NAME = None

def setup_test_image():
    """Create a test image if it doesn't exist"""
    if not os.path.exists(TEST_IMAGE_PATH):
        # Create a simple test image
        array = np.zeros((100, 100, 3), dtype=np.uint8)
        array[25:75, 25:75] = [255, 255, 255]  # White square in center
        save_np_as_image(array, TEST_IMAGE_PATH)

def cleanup():
    """Clean up test files"""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    if os.path.exists(TEST_IMAGE_PATH):
        os.remove(TEST_IMAGE_PATH)

@pytest.fixture(autouse=True)
def setup_and_cleanup():
    """Setup before each test and cleanup after"""
    setup_test_image()
    yield
    cleanup()

def test_encrypt_endpoint():
    """Test the encryption endpoint"""
    global ENCRYPTION_KEY, ENCRYPTED_FILE_NAME
    
    with open(TEST_IMAGE_PATH, "rb") as f:
        response = client.post(
            "/api/encrypt",
            files={"file": ("test_image.tiff", f, "image/TIFF")}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "encryption_key" in data
    assert "encrypted_id" in data
    assert "preview_image_path" in data
    assert "encrypted_file_path" in data
    
    # Store values for decryption test
    ENCRYPTION_KEY = data["encryption_key"]
    ENCRYPTED_FILE_NAME = data["encrypted_id"]
    
    # Verify files were created
    assert os.path.exists(os.path.join(TEST_ENC_DIR, f"{ENCRYPTED_FILE_NAME}.npy"))
    assert os.path.exists(os.path.join(TEST_ENC_DIR, f"{ENCRYPTED_FILE_NAME}.tiff"))
    assert os.path.exists(os.path.join(TEST_PREVIEW_DIR, f"{ENCRYPTED_FILE_NAME}_preview.png"))

def test_decrypt_endpoint():
    """Test the decryption endpoint"""
    if not (ENCRYPTION_KEY and ENCRYPTED_FILE_NAME):
        pytest.skip("Encryption test did not run or failed")
    
    response = client.post(
        "/api/decrypt",
        data={"filename": ENCRYPTED_FILE_NAME, "key": ENCRYPTION_KEY}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff"
    
    # Verify decrypted file was created
    dec_path = os.path.join(TEST_DEC_DIR, f"{ENCRYPTED_FILE_NAME}_decrypted.tiff")
    assert os.path.exists(dec_path)
    
    # Verify decrypted image can be opened
    decrypted_image = Image.open(dec_path)
    assert decrypted_image is not None 