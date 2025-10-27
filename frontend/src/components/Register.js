import React, { useState } from 'react';
import SiteLayout from './layout/SiteLayout';

function Register({ onNavigateToLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [voterId, setVoterId] = useState('');
  const [nationalId, setNationalId] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [captcha, setCaptcha] = useState('');
  const [photoDataUrl, setPhotoDataUrl] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    try {
      const payload = {
        username,
        password,
        voter_id: voterId,
        national_id: nationalId,
        email,
        phone,
        captcha: captcha || 'dev-ok',
        photo: photoDataUrl
      };

      const response = await fetch('http://localhost:5000/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }
      
      setSuccess('Registration successful! You can now login.');
      setUsername('');
      setPassword('');
      setConfirmPassword('');
      setVoterId('');
      setNationalId('');
      setEmail('');
      setPhone('');
      setCaptcha('');
      setPhotoDataUrl('');
      
      // Automatically redirect to login after 2 seconds
      setTimeout(() => {
        onNavigateToLogin();
      }, 2000);
    } catch (err) {
      setError(err.message);
    }
  };

  const onSelectPhoto = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setPhotoDataUrl(reader.result);
    reader.readAsDataURL(file);
  };

  return (
    <SiteLayout onLoginClick={onNavigateToLogin} onRegisterClick={() => {}} isLoggedIn={false}>
      <div className="eci-content">
        <div className="eci-card">
          <h2 style={{ marginTop: 0 }}>Register</h2>
          {error && <div className="alert alert-danger">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}
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
            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                type="password"
                className="form-control"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="voterId">Voter ID</label>
              <input
                type="text"
                className="form-control"
                id="voterId"
                value={voterId}
                onChange={(e) => setVoterId(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="nationalId">National ID</label>
              <input
                type="text"
                className="form-control"
                id="nationalId"
                value={nationalId}
                onChange={(e) => setNationalId(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                className="form-control"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="phone">Phone (optional)</label>
              <input
                type="tel"
                className="form-control"
                id="phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="photo">Photo</label>
              <input
                type="file"
                className="form-control"
                id="photo"
                accept="image/*"
                onChange={onSelectPhoto}
                required
              />
              {photoDataUrl && (
                <div style={{ marginTop: 8 }}>
                  <img src={photoDataUrl} alt="preview" style={{ maxWidth: 160, borderRadius: 6 }} />
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="captcha">Captcha</label>
              <input
                type="text"
                className="form-control"
                id="captcha"
                value={captcha}
                onChange={(e) => setCaptcha(e.target.value)}
                required
              />
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

export default Register;