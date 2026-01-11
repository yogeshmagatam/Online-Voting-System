import React, { useState } from 'react';
import SiteLayout from './layout/SiteLayout.jsx';

function Login({ onLogin, onNavigateToRegister, onNavigateToHome }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [otpRequired, setOtpRequired] = useState(false);
  const [otpDeliveryMethod, setOtpDeliveryMethod] = useState('');
  const [userId, setUserId] = useState(''); // Store user_id for OTP verification
  const [isResending, setIsResending] = useState(false);
  const [resendInfo, setResendInfo] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      if (!otpRequired) {
        // Step 1: Submit username and password to get OTP
        if (!username || !password) {
          setIsLoading(false);
          throw new Error('Please enter both username and password');
        }

        const response = await fetch('http://localhost:5000/api/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            username, 
            password,
            mfa_code: '' 
          }),
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          setIsLoading(false);
          throw new Error(data.error || 'Login failed');
        }

        // Check if MFA is required (backend returns mfa_required, not otp_required)
        if (data.mfa_required) {
          setOtpRequired(true);
          setUserId(data.user_id); // Store user_id for OTP verification
          setOtpDeliveryMethod(data.mfa_type);
          setOtpCode('');
          setError('');
          setIsLoading(false);
          return;
        }

        // Direct login for admin (no MFA required)
        if (data.access_token && data.role) {
          onLogin(data.access_token, data.role);
          return;
        }

        setIsLoading(false);
        throw new Error('Login failed - no token received');

      } else {
        // Step 2: Verify the 4-digit OTP
        if (!otpCode) {
          setIsLoading(false);
          throw new Error('Please enter the OTP code');
        }

        if (otpCode.length !== 4) {
          setIsLoading(false);
          throw new Error('OTP must be exactly 4 digits');
        }

        if (!otpCode.match(/^\d{4}$/)) {
          setIsLoading(false);
          throw new Error('OTP must be exactly 4 digits (0-9 only)');
        }

        const response = await fetch('http://localhost:5000/api/verify-otp', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            user_id: userId,
            otp: otpCode
          }),
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          setIsLoading(false);
          throw new Error(data.error || 'OTP verification failed');
        }

        // Check if password change is required
        if (data.require_password_change) {
          alert('Your password has expired or is new. Please change it after logging in.');
        }

        // Success - call onLogin with token and role
        onLogin(data.access_token, data.role);
      }
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (!userId) return;
    setIsResending(true);
    setResendInfo('');
    setError('');
    try {
      const resp = await fetch('http://localhost:5000/api/resend-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || 'Failed to resend OTP');
      setResendInfo('A new code has been sent to your email.');
    } catch (e) {
      setError(e.message);
    } finally {
      setIsResending(false);
    }
  };

  return (
    <SiteLayout onLoginClick={() => {}} onRegisterClick={onNavigateToRegister} isLoggedIn={false}>
      <div className="eci-content">
        <div className="eci-card">
          <h2 style={{ marginTop: 0 }}>Login</h2>
          {error && <div className="alert alert-danger">{error}</div>}
          <form onSubmit={handleSubmit}>
            {!otpRequired ? (
              <>
                <div className="form-group">
                  <label htmlFor="username">Username</label>
                  <input
                    type="text"
                    className="form-control"
                    id="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    disabled={isLoading}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="password">Password</label>
                  <div style={{ position: 'relative' }}>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      className="form-control"
                      id="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      disabled={isLoading}
                      style={{ paddingRight: 44 }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
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
                      disabled={isLoading}
                    >
                      {showPassword ? (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M17.94 17.94A10.94 10.94 0 0 1 12 20C5 20 1 12 1 12a21.77 21.77 0 0 1 5.06-6.95"/><path d="M1 1l22 22"/><path d="M9.88 9.88A3 3 0 0 0 12 15 3 3 0  0 0 14.12 14.12"/><path d="M16.12 7.88A10.94 10.94 0 0 1 23 12s-4 8-11 8a10.94 10.94 0 0 1-7.12-2.12"/></svg>
                      ) : (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                      )}
                    </button>
                  </div>
                </div>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={isLoading}
                >
                  {isLoading ? 'Logging in...' : 'Login'}
                </button>
              </>
            ) : (
              <>
                <div className="alert alert-info">
                  A 4-digit verification code has been sent to your {otpDeliveryMethod}. Please enter it below.
                </div>
                {resendInfo && <div className="alert alert-success">{resendInfo}</div>}
                <div className="form-group">
                  <label htmlFor="otpCode">4-Digit OTP Code</label>
                  <input
                    type="text"
                    className="form-control"
                    id="otpCode"
                    value={otpCode}
                    onChange={(e) => {
                      // Only allow digits
                      const value = e.target.value.replace(/\D/g, '');
                      setOtpCode(value);
                    }}
                    placeholder="0000"
                    required
                    maxLength="4"
                    disabled={isLoading}
                    inputMode="numeric"
                    autoComplete="off"
                  />
                </div>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={isLoading || otpCode.length !== 4}
                >
                  {isLoading ? 'Verifying...' : 'Verify OTP'}
                </button>
                <button
                  type="button"
                  className="btn btn-link"
                  onClick={handleResendOtp}
                  disabled={isResending}
                  style={{ marginLeft: '8px' }}
                >
                  {isResending ? 'Resending…' : 'Resend OTP'}
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => {
                    setOtpRequired(false);
                    setOtpCode('');
                    setOtpDeliveryMethod('');
                    setResendInfo('');
                    setError('');
                    setIsLoading(false);
                  }}
                  style={{ marginLeft: '8px' }}
                  disabled={isLoading}
                >
                  Back to Login
                </button>
              </>
            )}
          </form>
          <div style={{ marginTop: '16px' }}>
            <p>Don't have an account? <button className="eci-link" onClick={onNavigateToRegister}>Register</button></p>
          </div>
        </div>
      </div>
    </SiteLayout>
  );
}

export default Login;
