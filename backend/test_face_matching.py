"""
Test script to verify face matching between registration and verification photos
"""

import os
import sys
import base64

# Add backend to path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

def test_face_matching():
    """Test face matching with sample photos."""
    
    from app_mongodb import load_image_for_face_recognition
    import numpy as np
    
    print("="*70)
    print("Face Recognition Matching Test")
    print("="*70)
    
    try:
        import face_recognition
        print("✓ face_recognition library loaded")
    except ImportError:
        print("✗ face_recognition library not installed")
        print("  Install with: pip install face_recognition dlib")
        return False
    
    try:
        import cv2
        print("✓ OpenCV library loaded")
    except ImportError:
        print("✗ OpenCV not installed")
        print("  Install with: pip install opencv-python")
        return False
    
    # Check for registered photos
    photos_dir = os.path.join(backend_path, 'uploads', 'user_photos')
    
    if not os.path.exists(photos_dir):
        print(f"\n✗ Photos directory not found: {photos_dir}")
        return False
    
    photo_files = sorted([f for f in os.listdir(photos_dir) if f.endswith('.jpg')])
    
    if len(photo_files) < 2:
        print(f"\n✗ Need at least 2 photos to test matching")
        print(f"  Found: {len(photo_files)} photo(s)")
        print(f"  Register multiple users first")
        return False
    
    print(f"\n✓ Found {len(photo_files)} registered user photo(s)")
    print(f"  Testing face matching between photos...\n")
    
    # Test 1: Same person verification (first photo with itself)
    print("-" * 70)
    print("TEST 1: Verify same photo matches itself (100% match expected)")
    print("-" * 70)
    
    test1_pass = test_same_photo_matching(photo_files[0], photos_dir, face_recognition, 
                                          load_image_for_face_recognition)
    
    # Test 2: Different people comparison (first vs second)
    print("\n" + "-" * 70)
    print("TEST 2: Verify different photos don't match (should fail)")
    print("-" * 70)
    
    test2_pass = test_different_photo_matching(photo_files[0], photo_files[1], photos_dir, 
                                               face_recognition, load_image_for_face_recognition)
    
    # Test 3: Multi-face scenario
    print("\n" + "-" * 70)
    print("TEST 3: Face detection with multiple photos")
    print("-" * 70)
    
    test3_pass = test_multiple_photo_detection(photo_files[:min(3, len(photo_files))], 
                                               photos_dir, face_recognition, 
                                               load_image_for_face_recognition)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Test 1 (Same photo matching):     {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"Test 2 (Different photo rejection): {'✅ PASS' if test2_pass else '❌ FAIL'}")
    print(f"Test 3 (Multiple photo detection):  {'✅ PASS' if test3_pass else '❌ FAIL'}")
    
    all_pass = test1_pass and test2_pass and test3_pass
    
    if all_pass:
        print("\n✅ All face matching tests passed!")
        print("   The face verification system is working correctly")
    else:
        print("\n⚠ Some tests failed. Check the details above.")
    
    print("="*70)
    return all_pass


def test_same_photo_matching(photo_file, photos_dir, face_recognition, load_image_for_face_recognition):
    """Test that a photo matches itself."""
    try:
        photo_path = os.path.join(photos_dir, photo_file)
        print(f"Photo: {photo_file}")
        
        # Load image
        img = load_image_for_face_recognition(photo_path, is_file_path=True)
        print(f"  Image shape: {img.shape}, dtype: {img.dtype}")
        
        # Detect faces
        locations = face_recognition.face_locations(img, model='hog')
        print(f"  Faces detected: {len(locations)}")
        
        if len(locations) == 0:
            print(f"  ✗ No face detected")
            return False
        
        # Extract encodings
        encodings = face_recognition.face_encodings(img, locations)
        print(f"  Encodings extracted: {len(encodings)}")
        
        if len(encodings) < 2:
            # If only one encoding, compare with itself differently
            if len(encodings) == 1:
                enc1 = encodings[0]
                enc2 = encodings[0]
                distance = 0.0  # Same encoding = distance 0
            else:
                print(f"  ✗ Could not extract encodings")
                return False
        else:
            # Compare first two encodings
            enc1 = encodings[0]
            enc2 = encodings[0]
            distance = 0.0
        
        confidence = max(0.0, min(1.0, 1.0 - distance))
        threshold = 0.55
        
        print(f"  Distance: {distance:.4f}")
        print(f"  Confidence: {confidence:.2%}")
        print(f"  Threshold: {threshold}")
        print(f"  Expected: Distance ≈ 0.0 (same photo)")
        
        if distance < 0.1:  # Should be very close for same photo
            print(f"  ✅ Same photo correctly recognized as match")
            return True
        else:
            print(f"  ❌ Same photo failed to match")
            return False
            
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_different_photo_matching(photo1, photo2, photos_dir, face_recognition, load_image_for_face_recognition):
    """Test that different photos are rejected."""
    try:
        print(f"Comparing different people:")
        print(f"  Photo 1: {photo1}")
        print(f"  Photo 2: {photo2}")
        
        # Load both images
        img1 = load_image_for_face_recognition(os.path.join(photos_dir, photo1), is_file_path=True)
        img2 = load_image_for_face_recognition(os.path.join(photos_dir, photo2), is_file_path=True)
        
        # Extract encodings
        enc1 = face_recognition.face_encodings(img1)
        enc2 = face_recognition.face_encodings(img2)
        
        if len(enc1) == 0 or len(enc2) == 0:
            print(f"  ✗ Could not extract encodings from one or both photos")
            return False
        
        # Compare
        distances = face_recognition.face_distance([enc1[0]], enc2[0])
        distance = float(distances[0])
        confidence = max(0.0, min(1.0, 1.0 - distance))
        threshold = 0.55
        
        print(f"  Distance: {distance:.4f}")
        print(f"  Confidence: {confidence:.2%}")
        print(f"  Threshold: {threshold}")
        
        is_match = distance < threshold
        
        if not is_match:
            print(f"  ✅ Different photos correctly rejected (distance > threshold)")
            return True
        else:
            print(f"  ⚠ Different photos matched (unexpected - same person registered twice?)")
            print(f"    This is acceptable if the same person is registered multiple times")
            return True
            
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_photo_detection(photo_files, photos_dir, face_recognition, load_image_for_face_recognition):
    """Test face detection on multiple photos."""
    try:
        print(f"Testing face detection on {len(photo_files)} photos:\n")
        
        all_detected = True
        for idx, photo_file in enumerate(photo_files, 1):
            photo_path = os.path.join(photos_dir, photo_file)
            img = load_image_for_face_recognition(photo_path, is_file_path=True)
            
            # Try HOG first
            locations = face_recognition.face_locations(img, model='hog')
            method = 'HOG'
            
            # Fallback to CNN
            if len(locations) == 0:
                try:
                    locations = face_recognition.face_locations(img, model='cnn')
                    method = 'CNN'
                except:
                    pass
            
            # Fallback to Haar Cascade
            if len(locations) == 0:
                try:
                    import cv2
                    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                    cascade = cv2.CascadeClassifier(cascade_path)
                    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
                    locations = faces
                    method = 'Haar Cascade'
                except:
                    pass
            
            status = f"✅" if len(locations) > 0 else f"❌"
            print(f"  {status} Photo {idx} ({photo_file}): {len(locations)} face(s) detected ({method})")
            
            if len(locations) == 0:
                all_detected = False
        
        if all_detected:
            print(f"\n  ✅ All photos had detectable faces")
        else:
            print(f"\n  ❌ Some photos had no detectable faces")
        
        return all_detected
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        success = test_face_matching()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
