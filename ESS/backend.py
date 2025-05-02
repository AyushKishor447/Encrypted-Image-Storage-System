from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from PIL import Image
import numpy as np
import os

from api.encrypt import encrypt_img
from api.decrypt import decrypt_img
from api.preview import generate_preview
from utils.utils import save_encrypted_array, load_encrypted_array, save_np_as_image

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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

# === API MODELS ===
class Item(BaseModel):
    id: str
    name: str
    type: str
    preview: str

# === LIST ITEMS ===
@app.get("/api/items", response_model=list[Item])
def list_items():
    items = []
    for fname in os.listdir(STORAGE_PREVIEW):
        if fname.endswith(".tiff"):
            base = os.path.splitext(fname)[0]
            items.append(Item(
                id=base,
                name=base.replace("_preview", ""),
                type="file",
                preview=f"/api/preview/{base}"
            ))
    return items

# === PREVIEW ENDPOINT ===
@app.get("/api/preview/{item_id}")
def get_preview(item_id: str):
    path = os.path.join(STORAGE_PREVIEW, f"{item_id}.tiff")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Preview not found")
    return FileResponse(path, media_type="image/tiff")

# === ENCRYPTION ===
@app.post("/api/encrypt", response_class=JSONResponse)
async def encrypt_endpoint(file: UploadFile = File(...)):
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
    preview_path = os.path.join(STORAGE_PREVIEW, f"{enc_id}_preview.tiff")

    save_encrypted_array(encrypted_array, npy_path)
    save_np_as_image(encrypted_array, enc_view_path)
    save_np_as_image(generate_preview(array), preview_path)

    return {
        "message": "✅ Encryption successful",
        "encryption_key": str(key),
        "preview_id": f"{enc_id}_preview",
        "encrypted_id": enc_id,
        "preview_image_path": f"/storage/preview/{enc_id}_preview.tiff"
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
