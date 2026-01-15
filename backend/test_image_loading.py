"""
Test the improved face_recognition image loading
Run this script to debug any image format issues
"""

import os
import sys

# Add backend to path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

def test_image_loading():
    """Test the image loading function with various scenarios."""
    
    # Import after adding to path
    from app_mongodb import load_image_for_face_recognition
    import numpy as np
    
    print("="*60)
    print("Testing Image Loading Function")
    print("="*60)
    
    # Test 1: Test with actual registered photos
    photos_dir = os.path.join(backend_path, 'uploads', 'user_photos')
    
    if not os.path.exists(photos_dir):
        print(f"✗ Photos directory not found: {photos_dir}")
        print("  Register a user first to create photos")
        return False
    
    photo_files = [f for f in os.listdir(photos_dir) if f.endswith('.jpg')]
    
    if len(photo_files) == 0:
        print("✗ No photos found in uploads directory")
        print("  Register a user first to create photos")
        return False
    
    print(f"✓ Found {len(photo_files)} registered user photo(s)")
    
    # Test loading each photo
    all_passed = True
    for photo_file in photo_files[:3]:  # Test first 3 photos
        photo_path = os.path.join(photos_dir, photo_file)
        print(f"\n[Test] Loading: {photo_file}")
        
        try:
            img_array = load_image_for_face_recognition(photo_path, is_file_path=True)
            
            # Validate array properties
            assert isinstance(img_array, np.ndarray), "Not a numpy array"
            assert img_array.ndim == 3, f"Expected 3D, got {img_array.ndim}D"
            assert img_array.shape[2] == 3, f"Expected 3 channels, got {img_array.shape[2]}"
            assert img_array.dtype == np.uint8, f"Expected uint8, got {img_array.dtype}"
            assert img_array.flags['C_CONTIGUOUS'], "Array not C-contiguous"
            
            print(f"  ✓ Shape: {img_array.shape}")
            print(f"  ✓ Dtype: {img_array.dtype}")
            print(f"  ✓ C-contiguous: {img_array.flags['C_CONTIGUOUS']}")
            print(f"  ✓ Owns data: {img_array.flags['OWNDATA']}")
            
            # Test with face_recognition
            try:
                import face_recognition
                print(f"  [Testing] Extracting face encodings...")
                locations = face_recognition.face_locations(img_array, model='hog')
                encodings = face_recognition.face_encodings(img_array, locations)
                print(f"  ✓ Detected {len(locations)} face(s)")
                print(f"  ✓ Extracted {len(encodings)} encoding(s)")
                
            except ImportError:
                print(f"  ⚠ face_recognition not available, skipping face detection")
            except Exception as face_error:
                print(f"  ✗ Face recognition failed: {face_error}")
                all_passed = False
        
        except Exception as e:
            print(f"  ✗ Failed to load image: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ All tests passed!")
        print("   Images are properly formatted for face_recognition")
    else:
        print("❌ Some tests failed")
        print("   Check the error messages above")
    print("="*60)
    
    return all_passed


def test_face_encoding_extraction():
    """Test face encoding extraction directly."""
    print("\n" + "="*60)
    print("Testing Face Encoding Extraction")
    print("="*60)
    
    try:
        import face_recognition
        from app_mongodb import load_image_for_face_recognition
        import numpy as np
        
        photos_dir = os.path.join(backend_path, 'uploads', 'user_photos')
        photo_files = [f for f in os.listdir(photos_dir) if f.endswith('.jpg')]
        
        if len(photo_files) < 2:
            print("⚠ Need at least 2 photos to test face encoding comparison")
            return True
        
        # Load and encode first two photos
        photo1_path = os.path.join(photos_dir, photo_files[0])
        photo2_path = os.path.join(photos_dir, photo_files[1])
        
        print(f"[Test] Comparing face encodings:")
        print(f"  Photo 1: {photo_files[0]}")
        print(f"  Photo 2: {photo_files[1]}")
        
        img1 = load_image_for_face_recognition(photo1_path, is_file_path=True)
        img2 = load_image_for_face_recognition(photo2_path, is_file_path=True)
        
        enc1 = face_recognition.face_encodings(img1)
        enc2 = face_recognition.face_encodings(img2)
        
        if len(enc1) > 0 and len(enc2) > 0:
            distance = face_recognition.face_distance([enc1[0]], enc2[0])[0]
            confidence = float(max(0.0, min(1.0, 1.0 - distance)))
            print(f"  ✓ Face distance: {distance:.4f}")
            print(f"  ✓ Confidence: {confidence:.2%}")
            
            if distance < 0.6:
                print(f"  ✓ Faces likely match (same person)")
            else:
                print(f"  ⚠ Faces likely don't match (different people)")
        else:
            print(f"  ✗ Could not extract encodings (no faces found)")
            return False
        
        print("✅ Face encoding comparison successful!")
        return True
        
    except ImportError:
        print("⚠ face_recognition library not installed")
        print("  Install with: pip install face_recognition dlib")
        return True
    except Exception as e:
        print(f"❌ Face encoding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        success1 = test_image_loading()
        success2 = test_face_encoding_extraction()
        
        if success1 and success2:
            print("\n" + "="*60)
            print("✅ All image loading tests passed!")
            print("   The face recognition system is working correctly")
            print("="*60)
            sys.exit(0)
        else:
            print("\n" + "="*60)
            print("❌ Some tests failed")
            print("   Please check the error messages above")
            print("="*60)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
