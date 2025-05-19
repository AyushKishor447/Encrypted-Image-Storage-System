import numpy as np
import os

def save_encrypted_array(np_array: np.ndarray, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.save(path, np_array)
    print(f"✅ Encrypted NumPy array saved to {path}.npy")

def load_encrypted_array(path: str) -> np.ndarray:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} not found!")
    return np.load(path, allow_pickle=True)


from PIL import Image
import os

def save_np_as_image(np_array: np.ndarray, output_path: str, mode:str = "TIFF"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image = Image.fromarray(np_array.astype('uint8'))
    if mode.upper() == "TIFF":
        image.save(output_path, format="TIFF", compression="tiff_lzw")
    else:
        image.save(output_path, format=mode)
    print(f"✅ Image saved to {output_path}")


import json

def save_metadata(original_filename: str, meta_path: str):
    ext = os.path.splitext(original_filename)[1]
    metadata = {
        "original_filename": original_filename,
        "original_extension": ext
    }
    with open(meta_path, 'w') as f:
        json.dump(metadata, f)


def load_metadata(meta_path: str):
    with open(meta_path, 'r') as f:
        return json.load(f)

