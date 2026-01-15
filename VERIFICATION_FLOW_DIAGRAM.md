# Identity Verification Flow Diagram

## Complete Registration and Verification Process

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VOTER REGISTRATION FLOW                          │
└─────────────────────────────────────────────────────────────────────┘

    START
      ↓
   User fills form
   (username, password, email, voter_id)
      ↓
   User uploads/captures photo
      ↓
   Frontend converts to base64
      ↓
   POST /api/register/voter
      ↓
   ┌─ Check if username exists
   │  ├─ YES → Return error: "Username already exists"
   │  └─ NO → Continue
   │
   ├─ Hash password with bcrypt
   │
   ├─ Create user document in MongoDB
   │
   ├─ Load image (PIL/OpenCV)
   │  ├─ Convert to RGB
   │  └─ Save as JPEG
   │
   ├─ Update user with photo_path
   │
   ├─ Generate OTP and send email
   │
   └─ Return: "User registered successfully"
      ↓
   User checks email for OTP
      ↓
   POST /api/verify-otp
      ↓
   ┌─ Verify OTP matches
   │  ├─ Valid → Issue JWT token
   │  └─ Invalid → Return error
   │
   └─ User logged in with JWT
      ↓
   REGISTRATION COMPLETE ✓


┌─────────────────────────────────────────────────────────────────────┐
│               IDENTITY VERIFICATION FLOW                            │
└─────────────────────────────────────────────────────────────────────┘

    User clicks "Verify Identity"
      ↓
   Frontend initializes webcam
      ↓
   User captures live face photo
      ↓
   Frontend converts to base64
      ↓
   POST /api/verify-identity (with JWT)
      ↓ [BACKEND PROCESSING]
      ↓
   ┌─ Load live photo (PIL/OpenCV)
   │
   ├─ DETECT FACE - Method 1: HOG
   │  ├─ Success → Go to encoding extraction
   │  └─ No face → Try Method 2
   │
   ├─ DETECT FACE - Method 2: CNN
   │  ├─ Success → Go to encoding extraction
   │  └─ No face → Try Method 3
   │
   ├─ DETECT FACE - Method 3: Haar Cascade
   │  ├─ Success → Go to encoding extraction
   │  └─ No face → REJECT: "No face detected"
   │
   ├─ VALIDATE FACE QUALITY
   │  ├─ Check: Face is 5-90% of frame
   │  ├─ Check: Only one face detected
   │  ├─ Check: Face positioning is reasonable
   │  └─ Issues found → REJECT with specific reason
   │
   ├─ LOAD REGISTRATION PHOTO
   │  ├─ Check: Photo file exists
   │  ├─ Load with PIL/OpenCV
   │  └─ Validate format (RGB, uint8)
   │
   ├─ EXTRACT ENCODINGS
   │  ├─ Extract from registration photo
   │  │  ├─ Success → 128D face encoding
   │  │  └─ Failure → REJECT: "Registration photo corrupted"
   │  │
   │  ├─ Extract from live photo
   │  │  ├─ Success → 128D face encoding
   │  │  └─ Failure → REJECT: "Could not process live photo"
   │
   ├─ COMPARE FACE ENCODINGS
   │  ├─ Calculate Euclidean distance
   │  ├─ Distance = 0.0 → Perfect match
   │  ├─ Distance = 0.3245 → Good match (67.55% confidence)
   │  ├─ Distance = 0.55 → Borderline (45% confidence)
   │  └─ Distance = 0.7+ → No match (low confidence)
   │
   ├─ CHECK THRESHOLD
   │  ├─ Distance < 0.55 → ✅ VERIFIED
   │  └─ Distance ≥ 0.55 → ❌ NOT VERIFIED
   │
   ├─ MARK USER AS VERIFIED
   │  ├─ Set identity_verified = true in database
   │  └─ Log verification attempt
   │
   └─ Return JSON response
      ↓
   Frontend shows result
      ↓
   VERIFICATION COMPLETE


┌─────────────────────────────────────────────────────────────────────┐
│                  VOTING WITH VERIFICATION                           │
└─────────────────────────────────────────────────────────────────────┘

    User wants to vote
      ↓
   POST /api/cast-vote
      ↓
   ┌─ Check: User is authenticated (JWT valid)
   │
   ├─ Check: User has completed identity verification
   │  ├─ YES → Continue
   │  └─ NO → REJECT: "You must verify identity first"
   │
   ├─ Check: User hasn't already voted
   │  ├─ YES → REJECT: "You have already voted"
   │  └─ NO → Continue
   │
   ├─ FRAUD DETECTION
   │  ├─ Check voting behavior
   │  ├─ Check IP address
   │  ├─ Check voting patterns
   │  └─ Assess fraud risk
   │
   ├─ RECORD VOTE
   │  ├─ Save vote to database
   │  ├─ Generate transaction ID
   │  ├─ Log verification attempt
   │  └─ Record vote metadata
   │
   └─ Return transaction ID
      ↓
   User vote recorded ✓


┌─────────────────────────────────────────────────────────────────────┐
│                    DISTANCE INTERPRETATION                          │
└─────────────────────────────────────────────────────────────────────┘

Face Distance    Confidence    Interpretation              Decision
──────────────────────────────────────────────────────────────────────
0.0 - 0.20       90-100%       Excellent match            ✅ ACCEPT
0.20 - 0.35      80-90%        Very good match            ✅ ACCEPT
0.35 - 0.55      45-80%        Good match                 ✅ ACCEPT
0.55 - 0.60      40-45%        Borderline                 ⚠️  BORDERLINE
0.60 - 0.75      25-40%        Weak match                 ❌ REJECT
0.75+            0-25%         Poor match / No match      ❌ REJECT

THRESHOLD: 0.55
├─ < 0.55: User verified ✅
└─ ≥ 0.55: Verification failed ❌


┌─────────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING FLOW                              │
└─────────────────────────────────────────────────────────────────────┘

Identity Verification Request
           ↓
    ┌─ No photo provided?
    │  └─ Return 400: "Live photo is required"
    │
    ├─ Image corrupted?
    │  └─ Return 500: "Failed to load image"
    │
    ├─ No face detected?
    │  └─ Return 400: "No face detected. Please ensure clear visibility"
    │
    ├─ Multiple faces detected?
    │  └─ Return 400: "Multiple faces detected. Please verify alone"
    │
    ├─ Face too small/large?
    │  └─ Return 400: "Face positioning incorrect. Move closer/farther"
    │
    ├─ No registration photo?
    │  └─ Return 400: "Must register with photo first"
    │
    ├─ Registration photo corrupted?
    │  └─ Return 500: "Re-register with new photo"
    │
    ├─ Face distance ≥ 0.55?
    │  ├─ If 0.55-0.60: Return 400: "Borderline match. Try again"
    │  └─ If > 0.60: Return 400: "Faces don't match"
    │
    ├─ Face distance < 0.55?
    │  ├─ Mark identity_verified = true
    │  ├─ Log success
    │  └─ Return 200: "Identity verified successfully"
    │
    └─ Unexpected error?
       └─ Return 500: "Face verification error"


┌─────────────────────────────────────────────────────────────────────┐
│                  SECURITY CHECKPOINTS                               │
└─────────────────────────────────────────────────────────────────────┘

Registration Checkpoints:
1. ✓ Photo is required
2. ✓ Photo is valid image format
3. ✓ Photo converts to RGB successfully
4. ✓ Photo saved securely with user ID
5. ✓ Path stored in database

Verification Checkpoints:
1. ✓ JWT token valid (user authenticated)
2. ✓ Photo is required
3. ✓ Photo loads successfully
4. ✓ Exactly one face detected (anti-spoofing)
5. ✓ Face properly positioned (5-90% of frame)
6. ✓ Face encoding can be extracted
7. ✓ Registration photo exists
8. ✓ Registration photo loads successfully
9. ✓ Face distance < 0.55 (strict matching)
10. ✓ User marked as verified
11. ✓ All attempts logged with IP/timestamp

Voting Checkpoints:
1. ✓ JWT token valid
2. ✓ User identity_verified = true (REQUIRED!)
3. ✓ User hasn't already voted
4. ✓ Fraud detection passed
5. ✓ Vote recorded in database
6. ✓ Transaction ID generated


┌─────────────────────────────────────────────────────────────────────┐
│                  TYPICAL VERIFICATION TIMES                         │
└─────────────────────────────────────────────────────────────────────┘

Operation                          Time
────────────────────────────────────────────────
Load live photo (PIL)              ~50ms
Face detection (HOG)               ~100ms
Face detection (CNN if needed)     ~300-500ms
Encoding extraction                ~50ms per face
Load registration photo            ~50ms
Encoding extraction from reg       ~50ms
Distance calculation               <1ms
Database updates                   ~10ms
────────────────────────────────────────────────
TOTAL (typical case)               ~200-300ms
TOTAL (worst case with CNN)        ~600-800ms


Key Points:
- Fast enough for real-time verification (<1 second)
- HOG is usually sufficient (most of the time)
- CNN provides fallback for difficult cases
- All operations logged and tracked
- Thread-safe and production-ready
```

## State Diagram

```
┌─────────────────────────────────────────────────┐
│           USER STATE TRANSITIONS                │
└─────────────────────────────────────────────────┘

                  UNREGISTERED
                       ↓
              [Register with photo]
                       ↓
                  REGISTERED
                 identity_verified = false
                       ↓
            [Complete identity verification]
                       ↓
                   VERIFIED
                 identity_verified = true
                       ↓
               [Can now vote]
                       ↓
                    VOTED
                 voted = true
                       ↓
            [No more voting allowed]
                       ↓
                  (End state)

Transitions:
├─ UNREGISTERED → REGISTERED: /api/register/voter (with photo)
├─ REGISTERED → VERIFIED: /api/verify-identity (face matches)
├─ VERIFIED → VOTED: /api/cast-vote (user casts vote)
└─ VOTED → (locked): No more voting allowed
```
