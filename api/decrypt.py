import numpy as np
import pandas as pd
import math
from numpy import asarray
import matplotlib.pyplot as plt
import os
import sys 
import hashlib 
if sys.version_info < (3, 6): 
    import sha3 
from PIL import Image
from queue import PriorityQueue
from scipy.integrate import odeint 
import cv2
import warnings

def key(img_matrix):
    byte_array_image = bytearray(img_matrix)
    s = hashlib.sha3_512() 
    s.update(byte_array_image)
    key = s.hexdigest()
    key_1 = (int(key[0:25],16)/(2**100)) 
    key_2 = (int(key[25:50],16)/(2**100)) 
    key_3 = 10*(int(key[50:75],16)/(2**100))  
    key_4 = 10*(int(key[75:100],16)/(2**100)) 
    key_5 = (int(key[100:128],16)/(2**100)) %256
    return key_1, key_2, key_3, key_4, key_5

def New_map(input_seed, itr):
    N = int(itr)
    x = np.zeros(N)
    y = np.zeros_like(x)
    x[0], y[0], a, q, initial_pixel = input_seed
    for i in range(N-1): 
        
        x[i+1] = (2*x[i]+ q*y[i]*(1-y[i]) ) %1 
        y[i+1] = (a*y[i]+ np.cos(4*np.pi*x[i+1])) %1 
        
    return x,y, initial_pixel
    

def decrypt_img(C,key):
    if len(C.shape) == 2:
        m, n = C.shape
        x, y, init_pixel = New_map(key, 500+m*n)
        x = x[500:]
        y = y[500:]
        X = np.argsort(x)
        Y = []
        for i in range(len(y)):
           Y.append(math.floor(y[i]*10**10)%(256))
        C1 = C.reshape(m*n)
        P1 = np.zeros_like(C1)
        for i in range(m*n-1,0,-1):
            P1[X[i]] = C1[i] ^ Y[X[i]] ^ C1[i-1]
        P1 = P1.reshape(m,n)
        return P1
    elif len(C.shape) == 3:
        m, n, d = C.shape
        x, y, init_pixel = New_map(key, 500+m*n)
        x = x[500:]
        y = y[500:]
        X = np.argsort(x)
        Y = []
        P3=[]
        for i in range(len(y)):
            Y.append(math.floor(y[i]*10**10)%(256))
        for i in range(d):
            C1 = C[:,:,i].reshape(m*n)
            P1 = np.zeros_like(C1)
            for i in range(m*n-1,0,-1):
                P1[X[i]] = C1[i] ^ Y[X[i]] ^ C1[i-1]
            P1 = P1.reshape(m,n)
            P3.append(P1)

        P3=np.stack(P3,axis=2)
        return P3
            