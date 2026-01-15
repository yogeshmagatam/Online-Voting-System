import React, { useState, useRef, useEffect } from 'react';

function IdentityVerification({ token, onVerificationComplete, onCancel }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [cameraError, setCameraError] = useState('');
  const [verificationDetails, setVerificationDetails] = useState(null);
  const [useFileUpload, setUseFileUpload] = useState(false);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  // Start camera
  const startCamera = async () => {
    try {
      setCameraError('');
      setError('');
      // Show the live preview UI immediately (like the Register page)
      setCameraActive(true);
      console.log('[Camera] Requesting camera access...');
      
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        },
        audio: false
      });

      console.log('[Camera] Stream obtained:', stream);
      console.log('[Camera] Video tracks:', stream.getVideoTracks());

      if (videoRef.current) {
        console.log('[Camera] Attaching stream to video element');
        videoRef.current.srcObject = stream;
        
        // Ensure video plays
        videoRef.current.play().then(() => {
          console.log('[Camera] Video is now playing');
        }).catch(err => {
          console.error('[Camera] Play error:', err);
        });
      } else {
        console.error('[Camera] videoRef.current is null');
      }
    } catch (err) {
      console.error('Camera error:', err);
      console.error('Error name:', err.name);
      console.error('Error message:', err.message);
      
      let errorMessage = 'Unable to access camera. Please check browser permissions or use the upload option.';
      
      if (err.name === 'NotAllowedError') {
        errorMessage = 'Camera access denied. Please allow camera permissions in your browser settings.';
      } else if (err.name === 'NotFoundError') {
        errorMessage = 'No camera device found. Please connect a camera or use the upload option.';
      } else if (err.name === 'NotReadableError') {
        errorMessage = 'Camera is in use by another application (Zoom, Teams, etc.). Please close those apps and try again.';
      } else if (err.name === 'OverconstrainedError') {
        errorMessage = 'Camera does not support the requested video resolution. Please try a different camera or use upload.';
      } else if (err.name === 'TypeError') {
        errorMessage = 'Camera access is not available. Please ensure you\'re using a secure (HTTPS) connection or localhost.';
      }
      
      setCameraError(errorMessage);
      // Hide camera UI and fall back to file upload if permission fails
      setCameraActive(false);
      setUseFileUpload(true);
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      setCameraActive(false);
    }
  };

  // Capture photo from video
  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const context = canvasRef.current.getContext('2d');
      canvasRef.current.width = videoRef.current.videoWidth;
      canvasRef.current.height = videoRef.current.videoHeight;
      
      // Mirror the image (selfie mode)
      context.translate(canvasRef.current.width, 0);
      context.scale(-1, 1);
      
      context.drawImage(videoRef.current, 0, 0);
      
      // Convert to base64
      const photoData = canvasRef.current.toDataURL('image/jpeg', 0.95);
      setCapturedPhoto(photoData);
      stopCamera();
      setError('');
    }
  };

  // Retake photo
  const retakePhoto = () => {
    setCapturedPhoto(null);
    startCamera();
  };

  // Handle file upload
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please upload a valid image file');
        return;
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('Image size must be less than 5MB');
        return;
      }

      const reader = new FileReader();
      reader.onload = (event) => {
        setCapturedPhoto(event.target.result);
        setError('');
      };
      reader.onerror = () => {
        setError('Failed to read file');
      };
      reader.readAsDataURL(file);
    }
  };

  // Submit verification
  const handleSubmitVerification = async () => {
    if (!capturedPhoto) {
      setError('Please capture or upload a photo first');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('http://localhost:5000/api/verify-identity', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          live_photo: capturedPhoto,
          camera_source: useFileUpload ? 'file_upload' : 'webcam'
        })
      });

      const data = await response.json();

      if (!response.ok) {
        // Check if token has expired (401 status with token error)
        if (response.status === 401 && (data.code === 'token_expired' || data.code === 'token_invalid' || data.code === 'token_missing')) {
          setError(`${data.message || 'Session expired. Please log in again.'}`);
          // Redirect to login after a short delay
          setTimeout(() => {
            localStorage.removeItem('token');
            window.location.href = '/login';
          }, 2000);
          return;
        }

        // Handle fraud detection responses
        if (data.fraud_indicators && data.fraud_indicators.length > 0) {
          setError(`Identity verification failed: ${data.fraud_indicators.join(', ')}`);
          setVerificationDetails({
            fraudDetected: true,
            indicators: data.fraud_indicators,
            livenessScore: data.liveness_score,
            spoofingConfidence: data.spoofing_confidence
          });
        } else {
          setError(data.error || 'Verification failed');
          if (data.face_match_confidence !== undefined) {
            setVerificationDetails({
              fraudDetected: false,
              faceMatchConfidence: data.face_match_confidence,
              faceDistance: data.face_distance
            });
          }
        }
        setCapturedPhoto(null);
        return;
      }

      setSuccess('✓ Identity verified successfully!');
      setVerificationDetails({
        verified: true,
        faceMatchConfidence: data.face_match_confidence,
        livenessScore: data.liveness_score,
        isGenuine: data.is_genuine
      });

      // Notify parent component
      setTimeout(() => {
        if (onVerificationComplete) {
          onVerificationComplete();
        }
      }, 1500);
    } catch (err) {
      console.error('Identity verification error:', err);
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        setError('Network error: Unable to connect to server. Please check your connection.');
      } else {
        setError(`Error: ${err.message}`);
      }
      setCapturedPhoto(null);
    } finally {
      setLoading(false);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div className="identity-verification-container" style={styles.container}>
      <div className="verification-card" style={styles.card}>
        <h3 style={styles.title}>Identity Verification</h3>
        <p style={styles.subtitle}>
          Please capture a clear photo of your face using your camera for identity verification.
        </p>

        {error && (
          <div className="alert alert-danger" style={styles.alert}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {success && (
          <div className="alert alert-success" style={styles.alert}>
            {success}
          </div>
        )}

        {verificationDetails && verificationDetails.verified && (
          <div className="verification-details" style={styles.details}>
            <p>
              <strong>Face Match Confidence:</strong> {(verificationDetails.faceMatchConfidence * 100).toFixed(1)}%
            </p>
            <p>
              <strong>Liveness Score:</strong> {(verificationDetails.livenessScore * 100).toFixed(1)}%
            </p>
            <p>
              <strong>Status:</strong> <span style={{ color: 'green' }}>✓ Genuine Person Detected</span>
            </p>
          </div>
        )}

        {verificationDetails && verificationDetails.fraudDetected && (
          <div className="fraud-warning" style={{ ...styles.details, backgroundColor: '#fff3cd', borderColor: '#ffc107' }}>
            <p>
              <strong>⚠ Fraud Indicators Detected:</strong>
            </p>
            <ul>
              {verificationDetails.indicators.map((indicator, index) => (
                <li key={index}>
                  {indicator === 'multiple_faces_detected' && 'Multiple faces detected in image'}
                  {indicator === 'image_too_small' && 'Image too small - may be a screenshot'}
                  {indicator === 'no_face_detected' && 'No face detected in image'}
                  {indicator === 'detection_error' && 'Error during fraud detection'}
                </li>
              ))}
            </ul>
            {verificationDetails.livenessScore !== undefined && (
              <p><strong>Liveness Score:</strong> {(verificationDetails.livenessScore * 100).toFixed(1)}% (Below threshold)</p>
            )}
          </div>
        )}

        {verificationDetails && !verificationDetails.verified && !verificationDetails.fraudDetected && (
          <div className="face-mismatch-warning" style={{ ...styles.details, backgroundColor: '#f8d7da', borderColor: '#f5c6cb' }}>
            <p>
              <strong>Face Match Failed</strong>
            </p>
            <p>
              The captured face does not match your registered identity. 
            </p>
            {verificationDetails.faceMatchConfidence !== undefined && (
              <p>
                <strong>Match Confidence:</strong> {(verificationDetails.faceMatchConfidence * 100).toFixed(1)}%
              </p>
            )}
          </div>
        )}

        {/* Camera Section */}
        {!capturedPhoto && (
          <div style={styles.section}>
            {!cameraActive && !useFileUpload && (
              <div style={styles.buttonGroup}>
                <button
                  onClick={startCamera}
                  className="btn btn-primary"
                  style={{
                    ...styles.primaryButton,
                    display: 'inline-block',
                    visibility: 'visible',
                    opacity: 1
                  }}
                >
                  📷 Start Camera
                </button>
                <button
                  onClick={() => setUseFileUpload(true)}
                  className="btn btn-secondary"
                  style={{
                    ...styles.secondaryButton,
                    display: 'inline-block',
                    visibility: 'visible',
                    opacity: 1
                  }}
                >
                  📁 Upload Photo Instead
                </button>
              </div>
            )}

            {cameraActive && (
              <div style={styles.cameraSection}>
                <p style={{ color: '#28a745', fontWeight: 'bold', marginBottom: '10px' }}>
                  ✓ Camera Active - Live Preview
                </p>
                <div style={{ 
                  position: 'relative', 
                  width: '100%', 
                  backgroundColor: '#000',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <video
                    ref={videoRef}
                    autoPlay
                    muted
                    playsInline
                    style={{
                      width: '100%',
                      height: 'auto',
                      maxHeight: '400px',
                      minHeight: '300px',
                      display: 'block',
                      transform: 'scaleX(-1)',
                      backgroundColor: '#000'
                    }}
                    onLoadedMetadata={(e) => {
                      console.log('[Video] Metadata loaded, dimensions:', e.target.videoWidth, 'x', e.target.videoHeight);
                    }}
                    onPlaying={() => {
                      console.log('[Video] Video is playing now');
                    }}
                  />
                </div>
                <canvas ref={canvasRef} style={{ display: 'none' }} />
                
                <div style={styles.cameraInstructions}>
                  <p>📸 Position your face clearly in the center of the camera</p>
                  <p>✓ Ensure good lighting and no obstructions</p>
                  <p>✓ Face the camera directly</p>
                </div>

                <div style={{...styles.buttonGroup, justifyContent: 'center'}}>
                  <button
                    onClick={capturePhoto}
                    className="btn btn-success"
                    style={{
                      ...styles.successButton,
                      display: 'inline-block',
                      visibility: 'visible',
                      opacity: 1,
                      position: 'relative',
                      zIndex: 100
                    }}
                  >
                    📷 Capture Photo
                  </button>
                  <button
                    onClick={stopCamera}
                    className="btn btn-secondary"
                    style={{
                      ...styles.secondaryButton,
                      display: 'inline-block',
                      visibility: 'visible',
                      opacity: 1,
                      position: 'relative',
                      zIndex: 100
                    }}
                  >
                    ✕ Cancel Camera
                  </button>
                </div>
              </div>
            )}

            {useFileUpload && !cameraActive && (
              <div style={styles.fileUploadSection}>
                <label htmlFor="photo-upload" style={styles.fileLabel}>
                  📁 Select Photo from Your Device
                </label>
                <input
                  id="photo-upload"
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  style={styles.fileInput}
                />
                <button
                  onClick={() => setUseFileUpload(false)}
                  className="btn btn-secondary"
                  style={styles.secondaryButton}
                >
                  Back to Camera
                </button>
                {cameraError && (
                  <p style={{ color: '#dc3545', marginTop: '10px' }}>{cameraError}</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Photo Preview and Verification */}
        {capturedPhoto && (
          <div style={styles.section}>
            <div style={styles.previewSection}>
              <h4>📷 Preview</h4>
              <img
                src={capturedPhoto}
                alt="Captured"
                style={styles.previewImage}
              />
            </div>

            <div style={styles.buttonGroup}>
              <button
                onClick={handleSubmitVerification}
                disabled={loading}
                className="btn btn-success"
                style={{
                  ...styles.successButton,
                  display: 'inline-block',
                  visibility: 'visible',
                  opacity: loading ? 0.6 : 1,
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? '⏳ Verifying...' : '✓ Verify Identity'}
              </button>
              <button
                onClick={retakePhoto}
                disabled={loading}
                className="btn btn-secondary"
                style={{
                  ...styles.secondaryButton,
                  display: 'inline-block',
                  visibility: 'visible',
                  opacity: loading ? 0.6 : 1,
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                🔄 Retake Photo
              </button>
            </div>
          </div>
        )}

        {/* Close Button */}
        {!loading && (
          <div style={styles.closeButtonContainer}>
            <button
              onClick={onCancel}
              className="btn btn-outline-secondary"
              style={styles.closeButton}
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    padding: '20px'
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '30px',
    maxWidth: '500px',
    width: '100%',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    position: 'relative',
    zIndex: '1000'
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '10px',
    color: '#333'
  },
  subtitle: {
    color: '#666',
    marginBottom: '20px'
  },
  alert: {
    padding: '12px',
    marginBottom: '15px',
    borderRadius: '4px',
    fontSize: '14px'
  },
  details: {
    padding: '15px',
    backgroundColor: '#d4edda',
    border: '1px solid #c3e6cb',
    borderRadius: '4px',
    marginBottom: '15px',
    fontSize: '14px'
  },
  section: {
    marginBottom: '20px'
  },
  buttonGroup: {
    display: 'flex',
    gap: '15px',
    marginTop: '20px',
    flexWrap: 'wrap',
    width: '100%',
    justifyContent: 'center',
    alignItems: 'stretch'
  },
  primaryButton: {
    flex: '1 1 auto',
    minWidth: '140px',
    padding: '14px 24px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: '700',
    transition: 'background-color 0.3s ease, transform 0.2s ease',
    boxShadow: '0 4px 8px rgba(0,0,0,0.3)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  successButton: {
    flex: '1 1 auto',
    minWidth: '140px',
    padding: '14px 24px',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: '700',
    transition: 'background-color 0.3s ease, transform 0.2s ease',
    boxShadow: '0 4px 8px rgba(0,0,0,0.3)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  secondaryButton: {
    flex: '1 1 auto',
    minWidth: '140px',
    padding: '14px 24px',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: '700',
    transition: 'background-color 0.3s ease, transform 0.2s ease',
    boxShadow: '0 4px 8px rgba(0,0,0,0.3)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  closeButton: {
    width: '100%',
    padding: '10px',
    backgroundColor: 'white',
    color: '#6c757d',
    border: '1px solid #6c757d',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  closeButtonContainer: {
    marginTop: '20px',
    borderTop: '1px solid #eee',
    paddingTop: '15px'
  },
  cameraSection: {
    backgroundColor: '#f8f9fa',
    padding: '15px',
    borderRadius: '4px',
    marginBottom: '15px',
    position: 'relative',
    width: '100%'
  },
  video: {
    width: '100%',
    height: 'auto',
    maxHeight: '400px',
    borderRadius: '4px',
    marginBottom: '10px',
    backgroundColor: '#000',
    display: 'block',
    transform: 'scaleX(-1)',
    WebkitTransform: 'scaleX(-1)',
    objectFit: 'cover',
    minHeight: '300px'
  },
  cameraInstructions: {
    backgroundColor: '#e7f3ff',
    border: '1px solid #b3d9ff',
    borderRadius: '4px',
    padding: '12px',
    marginBottom: '15px',
    fontSize: '13px',
    color: '#004085'
  },
  previewSection: {
    backgroundColor: '#f8f9fa',
    padding: '15px',
    borderRadius: '4px',
    marginBottom: '15px'
  },
  previewImage: {
    width: '100%',
    borderRadius: '4px',
    marginTop: '10px'
  },
  fileUploadSection: {
    backgroundColor: '#f8f9fa',
    padding: '20px',
    borderRadius: '4px',
    textAlign: 'center',
    border: '2px dashed #ccc'
  },
  fileLabel: {
    display: 'block',
    marginBottom: '10px',
    fontWeight: '500',
    color: '#333'
  },
  fileInput: {
    display: 'block',
    width: '100%',
    marginBottom: '15px',
    padding: '8px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    cursor: 'pointer'
  }
};

export default IdentityVerification;
