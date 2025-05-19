import os

from api.encrypt import encrypt_img
from api.decrypt import decrypt_img
from api.preview import generate_preview
from api.validator import validate_img
from utils.utils import save_encrypted_array,save_np_as_image,load_encrypted_array,save_metadata,load_metadata
import matplotlib.pyplot as plt 
import matplotlib.image as img 
from PIL import Image
#testimage=img.read('photoshop_created_image5.png')
testimage=img.imread('lena_color.tiff')
# image_path = '\brain mri dataset sir\brainweb67.tif'
# # Open the image
# img = Image.open(image_path)
import cv2
img_gray = cv2.cvtColor(testimage, cv2.COLOR_BGR2GRAY)


STORAGE_ENCRYPTED = "storage/encrypted"
STORAGE_ENCRYPTED_VIEW = "storage/encrypted_view"
STORAGE_DECRYPTED = "storage/decrypted"
STORAGE_PREVIEW = "storage/preview"
METADATA_PATH="storage/metadata"

if not validate_img(img_gray):
    print("invalid image")
    exit(1)

filename = os.path.basename("lena_color")
imagename = os.path.basename("lena_color.tiff")
decimagename = os.path.basename("dec_img.tiff")
encname = os.path.basename("enc_lena_color.npy")
encrypted_path = os.path.join(STORAGE_ENCRYPTED, f"{encname}")
encrypted_view_path = os.path.join(STORAGE_ENCRYPTED_VIEW, f"{imagename}")
decrypted_path = os.path.join(STORAGE_DECRYPTED, f"{decimagename}")
preview_path = os.path.join(STORAGE_PREVIEW, f"{imagename}")
encrypted_image,KEY=encrypt_img(img_gray)
save_encrypted_array(encrypted_image,encrypted_path)
save_np_as_image(encrypted_image,encrypted_view_path)
preview_image=generate_preview(img_gray)
save_np_as_image(preview_image,preview_path)

encrypted_image_loaded=load_encrypted_array(encrypted_path)
decrypted_image=decrypt_img(encrypted_image_loaded,KEY)
save_np_as_image(decrypted_image,decrypted_path)

meta_data_path=os.path.join(METADATA_PATH,filename)
save_metadata(imagename,meta_data_path)

loaded_metadata=load_metadata(meta_data_path)
print(loaded_metadata)




