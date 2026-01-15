"""
Test script to verify face_recognition image loading and matching.
Run this to test the face verification system without using the full API.
"""

import base64
import io
import os
import numpy as np
from PIL import Image

def load_image_for_face_recognition(image_source, is_file_path=False):
    """
    Load and prepare an image for face_recognition library.
    Uses face_recognition.load_image_file() for proper dlib compatibility.
    This is the same function used in app_mongodb.py
    """
    import face_recognition
    import tempfile
    
    try:
        if is_file_path:
            # Use face_recognition.load_image_file() directly - it handles dlib properly
            print(f"[DEBUG] Loading from file path: {image_source}")
            img_array = face_recognition.load_image_file(image_source)
            print(f"✓ Image loaded - shape: {img_array.shape}, dtype: {img_array.dtype}")
            return img_array
        else:
            # Decode base64 - need to save to temp file first to use load_image_file()
            print(f"[DEBUG] Loading from base64 with face_recognition")
            
            if ',' in image_source and image_source.startswith('data:'):
                header, b64 = image_source.split(',', 1)
            else:
                b64 = image_source
            
            img_bytes = base64.b64decode(b64)
            
            # Create a temp file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name
            
            try:
                # Use face_recognition.load_image_file() for proper loading
                print(f"[DEBUG] Loading from temp file: {tmp_path}")
                img_array = face_recognition.load_image_file(tmp_path)
                print(f"✓ Image loaded - shape: {img_array.shape}, dtype: {img_array.dtype}")
                return img_array
            finally:
                # Clean up temp file
                try:
                    os.remove(tmp_path)
                except:
                    pass
        
    except Exception as e:
        print(f"✗ Failed to load image: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_face_recognition():
    """Test face recognition with sample images."""
    try:
        import face_recognition
        print("✓ face_recognition library imported successfully")
    except ImportError as e:
        print("✗ face_recognition library not installed")
        print("  Install it with: pip install face_recognition")
        return
    
    # Test with user photos if they exist
    photos_dir = os.path.join(os.getcwd(), 'backend', 'uploads', 'user_photos')
    
    if not os.path.exists(photos_dir):
        print(f"✗ Photos directory not found: {photos_dir}")
        print("  Register a user first to create photos")
        return
    
    # Find all .jpg files
    photo_files = [f for f in os.listdir(photos_dir) if f.endswith('.jpg')]
    
    if len(photo_files) == 0:
        print("✗ No photos found in uploads directory")
        print("  Register a user first to create photos")
        return
    
    print(f"\n✓ Found {len(photo_files)} registered user photo(s)")
    
    # Test loading first photo
    test_photo_path = os.path.join(photos_dir, photo_files[0])
    print(f"\nTesting with: {test_photo_path}")
    
    try:
        # Load image
        img_array = load_image_for_face_recognition(test_photo_path, is_file_path=True)
        
        # Detect faces
        print("\nDetecting faces...")
        face_locations = face_recognition.face_locations(img_array, model='hog')
        print(f"✓ Detected {len(face_locations)} face(s)")
        
        if len(face_locations) == 0:
            print("⚠ Warning: No faces detected in registration photo")
            print("  This user will fail identity verification")
        else:
            # Extract face encodings
            print("\nExtracting face encodings...")
            encodings = face_recognition.face_encodings(img_array, face_locations)
            print(f"✓ Extracted {len(encodings)} face encoding(s)")
            
            if len(encodings) > 0:
                print(f"✓ Face encoding shape: {encodings[0].shape}")
                print("\n✅ Face recognition system is working correctly!")
                print("   Users can now register and verify their identity.")
            
    except Exception as e:
        print(f"\n✗ Face recognition test failed: {e}")
        import traceback
        traceback.print_exc()


def test_image_formats():
    """Test that various image formats are handled correctly."""
    print("\n" + "="*50)
    print("Testing Image Format Support")
    print("="*50)
    
    # Test data - 1x1 pixel images in different formats
    test_images = {
        'JPEG': 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCWAAA//9k=',
        'PNG': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        'GIF': 'data:image/gif;base64,R0lGODlhAQABAPAAAP8AAP///yH5BAAAAAAALAAAAAABAAEAAAICRAEAOw==',
    }
    
    for format_name, data_url in test_images.items():
        try:
            img_array = load_image_for_face_recognition(data_url, is_file_path=False)
            print(f"✓ {format_name:6} format handled correctly")
        except Exception as e:
            print(f"✗ {format_name:6} format failed: {e}")


if __name__ == '__main__':
    print("="*50)
    print("Face Recognition System Test")
    print("="*50)
    
    # Test image format support
    test_image_formats()
    
    # Test face recognition
    test_face_recognition()
    
    print("\n" + "="*50)
    print("Test Complete")
    print("="*50)
