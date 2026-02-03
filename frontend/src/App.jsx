import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import './App.css';
import Login from './components/Login.jsx';
import Register from './components/Register.jsx';
import RegisterAdmin from './components/RegisterAdmin.jsx';
import Dashboard from './components/Dashboard.jsx';
import AdminDashboard from './components/AdminDashboard.jsx';
import VoterDashboard from './components/VoterDashboard.jsx';
import Home from './components/public/Home.jsx';
import Mission from './components/public/Mission.jsx';
import Security from './components/public/Security.jsx';
import Privacy from './components/public/Privacy.jsx';
import FAQ from './components/public/FAQ.jsx';
import Support from './components/public/Support.jsx';
import Accessibility from './components/public/Accessibility.jsx';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState('');
  const [userRole, setUserRole] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedRole = localStorage.getItem('userRole');
    if (storedToken) {
      setToken(storedToken);
      setUserRole(storedRole);
      setIsLoggedIn(true);
    }
  }, []);

  const handleLogin = (token, role) => {
    localStorage.setItem('token', token);
    localStorage.setItem('userRole', role);
    setToken(token);
    setUserRole(role);
    setIsLoggedIn(true);
    navigate('/dashboard', { replace: true });
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userRole');
    setToken('');
    setUserRole('');
    setIsLoggedIn(false);
  };

  const navigateToRegister = () => navigate('/register');
  const navigateToRegisterAdmin = () => navigate('/registerAdmin');
  const navigateToLogin = () => navigate('/login');
  const navigateToHome = () => navigate('/');
  const navigateToMission = () => navigate('/mission');
  const navigateToSecurity = () => navigate('/security');
  const navigateToPrivacy = () => navigate('/privacy');
  const navigateToFAQ = () => navigate('/faq');
  const navigateToSupport = () => navigate('/support');
  const navigateToAccessibility = () => navigate('/accessibility');

  // Render dashboard based on user role
  const renderDashboard = () => {
    switch (userRole) {
      case 'admin':
        return (
          <AdminDashboard
            token={token}
            onLogout={() => { handleLogout(); navigateToHome(); }}
            onNavigateToRegister={navigateToRegister}
            onNavigateToLogin={navigateToLogin}
            onNavigateToRegisterAdmin={navigateToRegisterAdmin}
            onNavigateToMission={navigateToMission}
            onNavigateToSecurity={navigateToSecurity}
            onNavigateToPrivacy={navigateToPrivacy}
            onNavigateToFAQ={navigateToFAQ}
            onNavigateToSupport={navigateToSupport}
            onNavigateToAccessibility={navigateToAccessibility}
          />
        );
      case 'voter':
        return (
          <VoterDashboard
            token={token}
            onLogout={() => { handleLogout(); navigateToHome(); }}
            onNavigateToRegister={navigateToRegister}
            onNavigateToLogin={navigateToLogin}
            onNavigateToRegisterAdmin={navigateToRegisterAdmin}
            onNavigateToMission={navigateToMission}
            onNavigateToSecurity={navigateToSecurity}
            onNavigateToPrivacy={navigateToPrivacy}
            onNavigateToFAQ={navigateToFAQ}
            onNavigateToSupport={navigateToSupport}
            onNavigateToAccessibility={navigateToAccessibility}
          />
        );
      default:
        return <Dashboard token={token} userRole={userRole} onLogout={() => { handleLogout(); navigateToHome(); }} />;
    }
  };

  return (
    <div className="App">
      <Routes>
        {/* Public routes */}
        <Route
          path="/"
          element={
            !isLoggedIn ? (
              <Home
                onLoginClick={navigateToLogin}
                onRegisterClick={navigateToRegister}
                onRegisterAdminClick={navigateToRegisterAdmin}
                onNavigateToHome={navigateToHome}
                onNavigateToMission={navigateToMission}
                onNavigateToSecurity={navigateToSecurity}
                onNavigateToPrivacy={navigateToPrivacy}
                onNavigateToFAQ={navigateToFAQ}
                onNavigateToSupport={navigateToSupport}
                onNavigateToAccessibility={navigateToAccessibility}
              />
            ) : (
              <Navigate to="/dashboard" replace />
            )
          }
        />
        <Route path="/login" element={!isLoggedIn ? <Login onLogin={handleLogin} onNavigateToRegister={navigateToRegister} onNavigateToHome={navigateToHome} /> : <Navigate to="/dashboard" replace />} />
        <Route path="/register" element={!isLoggedIn ? <Register onNavigateToLogin={navigateToLogin} /> : <Navigate to="/dashboard" replace />} />
        <Route path="/registerAdmin" element={!isLoggedIn ? <RegisterAdmin onNavigateToLogin={navigateToLogin} /> : <Navigate to="/dashboard" replace />} />

        {/* Public info pages, accessible to all */}
        <Route path="/mission" element={<Mission onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToMission={navigateToMission} onNavigateToSecurity={navigateToSecurity} onNavigateToPrivacy={navigateToPrivacy} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />} />
        <Route path="/security" element={<Security onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToMission={navigateToMission} onNavigateToSecurity={navigateToSecurity} onNavigateToPrivacy={navigateToPrivacy} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />} />
        <Route path="/privacy" element={<Privacy onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToMission={navigateToMission} onNavigateToSecurity={navigateToSecurity} onNavigateToPrivacy={navigateToPrivacy} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />} />
        <Route path="/faq" element={<FAQ onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />} />
        <Route path="/support" element={<Support onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />} />
        <Route path="/accessibility" element={<Accessibility onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />} />

        {/* Dashboard route */}
        <Route path="/dashboard" element={isLoggedIn ? renderDashboard() : <Navigate to="/login" replace />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
