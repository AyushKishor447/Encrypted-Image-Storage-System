from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
import os
from PIL import Image
import numpy as np
from api.encrypt import encrypt_img
from api.decrypt import decrypt_img
from utils.utils import save_encrypted_array, load_encrypted_array, save_np_as_image
from api.preview import generate_preview

app = FastAPI()

# @app.post("/encrypt/")
# async def encrypt_endpoint(file: UploadFile = File(...)):
#     filename = file.filename
#     basename = os.path.splitext(filename)[0]
#     temp_path = f"temp/{filename}"

#     # Save uploaded file to temp/
#     os.makedirs(os.path.dirname(temp_path), exist_ok=True)
#     with open(temp_path, "wb") as f:
#         f.write(await file.read())

#     # Encrypt the image (returns encrypted array and the key)
#     encrypted_array, key = encrypt_img(temp_path)

#     # Save encrypted array (for future decryption)
#     encrypted_array_path = f"storage/encrypted/{basename}.npy"
#     save_encrypted_array(encrypted_array, encrypted_array_path)

#     # Save encrypted array as a .tiff image for preview
#     preview_path = f"storage/preview/{basename}_enc.tiff"
#     save_np_as_image(encrypted_array, preview_path)

#     # Return the encryption key and preview image path
#     return JSONResponse(content={
#         "message": "✅ Encryption successful",
#         "encryption_key": key,
#         "preview_image_path": preview_path,
#         "encrypted_array_path": encrypted_array_path
#     })

@app.post("/encrypt/")
async def encrypt_endpoint(file: UploadFile = File(...)):
    contents = await file.read()
    temp_path = f"temp_uploads/{file.filename}"
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(contents)

    # 🛠 Load image as numpy array here
    img_pil = Image.open(temp_path)
    img_matrix = np.array(img_pil)

    encrypted_array, key = encrypt_img(img_matrix)  # pass the numpy array, NOT path

    encrypted_filename = os.path.splitext(file.filename)[0] + "_encrypted"
    encrypted_save_path = f"storage/encrypted/{encrypted_filename}.npy"
    save_encrypted_array(encrypted_array, encrypted_save_path)
    encrypted_view_path=f"storage/encrypted_view/{encrypted_filename}.tiff"
    save_np_as_image(encrypted_array,encrypted_view_path)

    # Also generate preview
    preview = generate_preview(img_matrix)
    preview_save_path = f"storage/preview/{encrypted_filename}_preview.tiff"
    save_np_as_image(preview, preview_save_path)

    return {
        "message": "✅ Image encrypted and saved successfully!",
        "encryption_key": str(key),
        "preview_image_path": preview_save_path,
        "encrypted_array_path": encrypted_save_path,
        "encrypted_view_path" : encrypted_view_path
    }

from fastapi import UploadFile, File, Form
from fastapi.responses import FileResponse
import os

@app.post("/decrypt/")
async def decrypt_endpoint(file: UploadFile = File(...), key: str = Form(...)):
    filename = file.filename
    basename = os.path.splitext(filename)[0]
    temp_path = f"temp/{filename}"

    # Save uploaded encrypted file to temp/
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Parse and validate the key string
    try:
        key_tuple = tuple(map(float, key.strip("()").split(",")))
        if len(key_tuple) != 5:
            raise ValueError("Key must have exactly 5 float elements.")
    except Exception as e:
        return {"error": f"Invalid key format: {str(e)}"}

    # Load the encrypted array
    encrypted_array = load_encrypted_array(temp_path)

    # Decrypt the image using the parsed key
    decrypted_image = decrypt_img(encrypted_array, key_tuple)

    # Save decrypted image as tiff
    decrypted_path = f"storage/decrypted/{basename}_dec.tiff"
    os.makedirs(os.path.dirname(decrypted_path), exist_ok=True)
    save_np_as_image(decrypted_image, decrypted_path)

    # Return the decrypted image
    return FileResponse(decrypted_path, media_type="image/tiff", filename=os.path.basename(decrypted_path))
