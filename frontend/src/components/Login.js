import React, { useState } from 'react';
import SiteLayout from './layout/SiteLayout';

function Login({ onLogin, onNavigateToRegister, onNavigateToHome }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [otpRequired, setOtpRequired] = useState(false);
  const [otpDeliveryMethod, setOtpDeliveryMethod] = useState('');
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

        // Check if OTP is required
        if (data.otp_required) {
          setOtpRequired(true);
          setOtpDeliveryMethod(data.otp_delivery_method);
          setOtpCode('');
          setError('');
          setIsLoading(false);
          return;
        }

        // This shouldn't happen with the new OTP system, but handle it just in case
        setIsLoading(false);
        throw new Error('OTP generation failed');

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

        const response = await fetch('http://localhost:5000/api/verify-login-otp', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            username, 
            otp_code: otpCode
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
                  <input
                    type="password"
                    className="form-control"
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={isLoading}
                  />
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
                  className="btn btn-secondary" 
                  onClick={() => {
                    setOtpRequired(false);
                    setOtpCode('');
                    setOtpDeliveryMethod('');
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