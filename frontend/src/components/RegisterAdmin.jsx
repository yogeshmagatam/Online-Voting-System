import React, { useEffect, useState } from 'react';
import SiteLayout from './layout/SiteLayout';

export default function RegisterAdmin({ onNavigateToLogin }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [captcha, setCaptcha] = useState('');
  const [captchaText, setCaptchaText] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const generateCaptcha = () => {
    const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const lowercase = 'abcdefghijklmnopqrstuvwxyz';
    const numbers = '0123456789';
    
    let text = '';
    // Ensure at least 2 uppercase letters
    for (let i = 0; i < 2; i++) {
      text += uppercase.charAt(Math.floor(Math.random() * uppercase.length));
    }
    // Ensure at least 2 lowercase letters
    for (let i = 0; i < 2; i++) {
      text += lowercase.charAt(Math.floor(Math.random() * lowercase.length));
    }
    // Ensure at least 2 numbers
    for (let i = 0; i < 2; i++) {
      text += numbers.charAt(Math.floor(Math.random() * numbers.length));
    }
    // Shuffle the result to mix uppercase, lowercase, and numbers
    text = text.split('').sort(() => Math.random() - 0.5).join('');
    setCaptchaText(text);
  };

  useEffect(() => {
    generateCaptcha();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!username || !email || !password || !confirmPassword) {
      setError('All fields are required');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (!captcha || captcha.trim().toUpperCase() !== captchaText.toUpperCase()) {
      setError('Incorrect captcha');
      setCaptcha('');
      generateCaptcha();
      return;
    }

    try {
      const response = await fetch('http://localhost:5000/api/register/admin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, captcha })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Registration failed');

      setSuccess('Admin registered successfully! You can now login.');
      setUsername('');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
      setCaptcha('');
      generateCaptcha();
      setTimeout(() => onNavigateToLogin(), 1500);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <SiteLayout onLoginClick={onNavigateToLogin} onRegisterClick={() => {}} isLoggedIn={false}>
      <div className="eci-content">
        <div className="eci-card" style={{ maxWidth: 520, margin: '20px auto' }}>
          <h2>Register as Admin</h2>
          <p style={{ color: '#666' }}>Create an admin account to monitor elections.</p>

          {error && <div className="alert alert-danger">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <form onSubmit={handleSubmit} className="form-group">
            <div className="form-group">
              <label>Username</label>
              <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} className="form-control" required />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="form-control" required />
            </div>
            <div className="form-group">
              <label>Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="form-control"
                  required
                  style={{ paddingRight: 44 }}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  style={{
                    position: 'absolute',
                    right: 8,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'transparent',
                    border: 'none',
                    padding: 4,
                    cursor: 'pointer',
                    color: '#555'
                  }}
                >
                  {showPassword ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20C5 20 1 12 1 12a21.77 21.77 0 0 1 5.06-6.95"/>
                      <path d="M1 1l22 22"/>
                      <path d="M9.88 9.88A3 3 0 0 0 12 15 3 3 0 0 0 14.12 14.12"/>
                      <path d="M16.12 7.88A10.94 10.94 0 0 1 23 12s-4 8-11 8a10.94 10.94 0 0 1-7.12-3.88"/>
                    </svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  )}
                </button>
              </div>
            </div>
            <div className="form-group">
              <label>Confirm Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="form-control"
                  required
                  style={{ paddingRight: 44 }}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((v) => !v)}
                  aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  style={{
                    position: 'absolute',
                    right: 8,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'transparent',
                    border: 'none',
                    padding: 4,
                    cursor: 'pointer',
                    color: '#555'
                  }}
                >
                  {showConfirmPassword ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20C5 20 1 12 1 12a21.77 21.77 0 0 1 5.06-6.95"/>
                      <path d="M1 1l22 22"/>
                      <path d="M9.88 9.88A3 3 0 0 0 12 15 3 3 0 0 0 14.12 14.12"/>
                      <path d="M16.12 7.88A10.94 10.94 0 0 1 23 12s-4 8-11 8a10.94 10.94 0 0 1-7.12-3.88"/>
                    </svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  )}
                </button>
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="captcha">Captcha</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <div
                  aria-label="captcha-image"
                  style={{
                    userSelect: 'none',
                    fontFamily: 'monospace',
                    fontSize: 22,
                    letterSpacing: 6,
                    padding: '8px 12px',
                    background: 'repeating-linear-gradient(45deg, #f5f5f5, #f5f5f5 10px, #eaeaea 10px, #eaeaea 20px)',
                    border: '1px solid #ddd',
                    borderRadius: 6,
                    transform: 'skewX(-6deg)'
                  }}
                >
                  {captchaText}
                </div>
                <button type="button" className="btn btn-secondary" onClick={generateCaptcha}>
                  Refresh
                </button>
              </div>
              <input
                type="text"
                className="form-control"
                id="captcha"
                value={captcha}
                onChange={(e) => setCaptcha(e.target.value)}
                placeholder="Enter the text above"
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Register Admin</button>
          </form>
        </div>
      </div>
    </SiteLayout>
  );
}
