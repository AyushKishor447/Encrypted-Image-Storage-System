import cv2
import numpy as np

# def generate_preview(image):
#     n,m,_=image.shape
#     img=image
#     img=cv2.GaussianBlur(img, (51, 51), 0)
#     noise = np.random.normal(0, 1, img.shape).astype(np.uint8)
#     noisy = cv2.add(img, noise)
#     for i in range(((int)(n/3))):
#         ii=np.random.randint(0,n-1)
#         for j in range(((int)(m/5))):
#             jj=np.random.randint(0,m-1)
#             noisy[ii][jj]=0
#     return noisy

def generate_preview(image):
    if len(image.shape)==2:
        n,m=image.shape
        img=image
        img=cv2.GaussianBlur(img, (51, 51), 0)
        noise = np.random.normal(0, 1, img.shape).astype(np.uint8)
        noisy = cv2.add(img, noise)
        for i in range(((int)(n/3))):
            ii=np.random.randint(0,n-1)
            for j in range(((int)(m/5))):
                jj=np.random.randint(0,m-1)
                noisy[ii,jj]=0
    elif len(image.shape)==3:
        n,m,_=image.shape
        img=image
        img=cv2.GaussianBlur(img, (51, 51), 0)
        noise = np.random.normal(0, 1, img.shape).astype(np.uint8)
        noisy = cv2.add(img, noise)
        for i in range(((int)(n/3))):
            ii=np.random.randint(0,n-1)
            for j in range(((int)(m/5))):
                jj=np.random.randint(0,m-1)
                noisy[ii,jj,:]=0
    return noisy