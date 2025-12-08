import React, { useEffect, useRef, useState } from 'react';
import SiteLayout from './layout/SiteLayout';

function CandidateRegister({ onNavigateToLogin, onNavigateToVoter }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [captcha, setCaptcha] = useState('');
  const [captchaText, setCaptchaText] = useState('');
  const [photoDataUrl, setPhotoDataUrl] = useState('');
  const [usingCamera, setUsingCamera] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const generateCaptcha = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let text = '';
    for (let i = 0; i < 6; i++) {
      text += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setCaptchaText(text);
  };

  useEffect(() => { generateCaptcha(); }, []);
  useEffect(() => () => { stopCamera(); }, []);

  const startCamera = async () => {
    try {
      setCameraError('');
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch (err) {
      console.error('Camera error:', err);
      setCameraError('Unable to access camera. Please check permissions or use Upload Photo.');
      setUsingCamera(false);
    }
  };

  const stopCamera = () => {
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
        streamRef.current = null;
      }
      if (videoRef.current) videoRef.current.srcObject = null;
    } catch (_) {}
  };

  const capturePhoto = () => {
    const video = videoRef.current;
    if (!video) return;
    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;
    const canvas = document.createElement('canvas');
    canvas.width = width; canvas.height = height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, width, height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    setPhotoDataUrl(dataUrl);
  };

  const onSelectPhoto = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setPhotoDataUrl(reader.result);
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setSuccess('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!captcha || captcha.trim().toUpperCase() !== captchaText.toUpperCase()) {
      setError('Incorrect captcha');
      generateCaptcha();
      return;
    }

    if (!photoDataUrl) {
      setError('Please provide a photo by uploading or capturing from camera');
      return;
    }

    try {
      const payload = {
        username,
        password,
        email,
        phone,
        captcha,
        photo: photoDataUrl
      };

      const response = await fetch('http://localhost:5000/api/register/candidate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Registration failed');

      setSuccess('Registration successful! You can now login.');
      setUsername(''); setPassword(''); setConfirmPassword('');
      setEmail(''); setPhone(''); setCaptcha(''); setPhotoDataUrl('');
      generateCaptcha(); stopCamera();

      setTimeout(() => onNavigateToLogin(), 2000);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <SiteLayout onLoginClick={onNavigateToLogin} onRegisterClick={() => {}} isLoggedIn={false}>
      <div className="eci-content">
        <div 
          className="eci-card" 
          style={{ 
            marginBottom: 16, 
            padding: 20, 
            background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)', 
            color: 'white', 
            textAlign: 'center',
            border: 'none',
            boxShadow: '0 4px 12px rgba(17, 153, 142, 0.3)'
          }}
        >
          <h3 style={{ margin: 0, marginBottom: 8, fontSize: '1.4rem' }}>Want to Vote?</h3>
          <p style={{ margin: 0, marginBottom: 16, opacity: 0.95, fontSize: '1rem' }}>
            Register as a voter to cast your vote in the election
          </p>
          <button 
            className="btn" 
            style={{ 
              background: 'white', 
              color: '#11998e', 
              border: 'none', 
              fontWeight: 'bold',
              padding: '10px 24px',
              fontSize: '1rem',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
            }} 
            onClick={onNavigateToVoter || (() => {})}
          >
            Register as Voter →
          </button>
        </div>
        <div className="eci-card">
          <h2 style={{ marginTop: 0 }}>Register as Candidate</h2>
          {error && <div className="alert alert-danger">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input type="text" className="form-control" id="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div style={{ position: 'relative' }}>
                <input type={showPassword ? 'text' : 'password'} className="form-control" id="password" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ paddingRight: 44 }} autoComplete="new-password" />
                <button type="button" onClick={() => setShowPassword(v => !v)} aria-label={showPassword ? 'Hide password' : 'Show password'} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 'none', padding: 4, cursor: 'pointer', color: '#555' }}>
                  {showPassword ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M17.94 17.94A10.94 10.94 0 0 1 12 20C5 20 1 12 1 12a21.77 21.77 0 0 1 5.06-6.95"/><path d="M1 1l22 22"/><path d="M9.88 9.88A3 3 0 0 0 12 15 3 3 0 0 0 14.12 14.12"/><path d="M16.12 7.88A10.94 10.94 0 0 1 23 12s-4 8-11 8a10.94 10.94 0 0 1-7.12-3.88"/></svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  )}
                </button>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <div style={{ position: 'relative' }}>
                <input type={showConfirmPassword ? 'text' : 'password'} className="form-control" id="confirmPassword" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required style={{ paddingRight: 44 }} autoComplete="new-password" />
                <button type="button" onClick={() => setShowConfirmPassword(v => !v)} aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 'none', padding: 4, cursor: 'pointer', color: '#555' }}>
                  {showConfirmPassword ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M17.94 17.94A10.94 10.94 0 0 1 12 20C5 20 1 12 1 12a21.77 21.77 0 0 1 5.06-6.95"/><path d="M1 1l22 22"/><path d="M9.88 9.88A3 3 0 0 0 12 15 3 3 0 0 0 14.12 14.12"/><path d="M16.12 7.88A10.94 10.94 0 0 1 23 12s-4 8-11 8a10.94 10.94 0 0 1-7.12-3.88"/></svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  )}
                </button>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input type="email" className="form-control" id="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>

            <div className="form-group">
              <label htmlFor="phone">Phone (optional)</label>
              <input type="tel" className="form-control" id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>

            <div className="form-group">
              <label htmlFor="photo">Photo</label>
              <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
                <button type="button" className={`btn ${usingCamera ? 'btn-primary' : 'btn-secondary'}`} onClick={async () => { setUsingCamera(true); await startCamera(); }}>Use Camera</button>
                <button type="button" className={`btn ${!usingCamera ? 'btn-primary' : 'btn-secondary'}`} onClick={() => { setUsingCamera(false); stopCamera(); }}>Upload Photo</button>
              </div>
              {usingCamera ? (
                <div>
                  {cameraError && <div className="alert alert-warning">{cameraError}</div>}
                  <div style={{ marginBottom: 8 }}>
                    <video ref={videoRef} style={{ width: 260, maxWidth: '100%', borderRadius: 6, background: '#000' }} muted playsInline />
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button type="button" className="btn btn-success" onClick={capturePhoto}>Capture Photo</button>
                    <button type="button" className="btn btn-outline-secondary" onClick={stopCamera}>Stop Camera</button>
                  </div>
                </div>
              ) : (
                <input type="file" className="form-control" id="photo" accept="image/*" onChange={onSelectPhoto} />
              )}
              {photoDataUrl && (
                <div style={{ marginTop: 8 }}>
                  <img src={photoDataUrl} alt="preview" style={{ maxWidth: 160, borderRadius: 6 }} />
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="captcha">Captcha</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <div aria-label="captcha-image" style={{ userSelect: 'none', fontFamily: 'monospace', fontSize: 22, letterSpacing: 6, padding: '8px 12px', background: 'repeating-linear-gradient(45deg, #f5f5f5, #f5f5f5 10px, #eaeaea 10px, #eaeaea 20px)', border: '1px solid #ddd', borderRadius: 6, transform: 'skewX(-6deg)' }}>{captchaText}</div>
                <button type="button" className="btn btn-secondary" onClick={generateCaptcha}>Refresh</button>
              </div>
              <input type="text" className="form-control" id="captcha" value={captcha} onChange={(e) => setCaptcha(e.target.value)} placeholder="Enter the text above" required />
            </div>

            <button type="submit" className="btn btn-primary">Register</button>
          </form>
          <div style={{ marginTop: '16px' }}>
            <p>Already have an account? <button className="eci-link" onClick={onNavigateToLogin}>Login</button></p>
          </div>
        </div>
      </div>
    </SiteLayout>
  );
}

export default CandidateRegister;
