#!/usr/bin/env python
import face_recognition
import numpy as np
from PIL import Image

photo = r'D:\Desktop_folder\Major_Project_clg\backend\backend\uploads\user_photos\6964a94ad203cd8cd8a2f504.jpg'
img = face_recognition.load_image_file(photo)
print(f'Original - Shape: {img.shape}, dtype: {img.dtype}')
print(f'Original - C_CONTIGUOUS: {img.flags["C_CONTIGUOUS"]}')

# Try workaround: Convert through PIL and back
print("\nTrying PIL workaround...")
pil_img = Image.fromarray(img, 'RGB')
img2 = np.array(pil_img, dtype=np.uint8)
print(f'After PIL - Shape: {img2.shape}, dtype: {img2.dtype}')
print(f'After PIL - C_CONTIGUOUS: {img2.flags["C_CONTIGUOUS"]}')

# Try HOG model on workaround
try:
    locs = face_recognition.face_locations(img2, model='hog')
    print(f'✓ HOG found {len(locs)} faces')
except Exception as e:
    print(f'✗ HOG failed: {e}')

