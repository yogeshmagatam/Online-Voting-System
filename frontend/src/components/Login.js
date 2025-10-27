import React, { useState } from 'react';
import SiteLayout from './layout/SiteLayout';

function Login({ onLogin, onNavigateToRegister, onNavigateToHome }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const response = await fetch('http://localhost:5000/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }
      
      onLogin(data.access_token, data.role);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <SiteLayout onLoginClick={() => {}} onRegisterClick={onNavigateToRegister} isLoggedIn={false}>
      <div className="eci-content">
        <div className="eci-card">
          <h2 style={{ marginTop: 0 }}>Login</h2>
          {error && <div className="alert alert-danger">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                type="text"
                className="form-control"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
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
              />
            </div>
            <button type="submit" className="btn btn-primary">Login</button>
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