import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './components/Login';
import Register from './components/Register';
import CandidateRegister from './components/CandidateRegister';
import Dashboard from './components/Dashboard';
import AdminDashboard from './components/AdminDashboard';
import VoterDashboard from './components/VoterDashboard';
import CandidateDashboard from './components/CandidateDashboard';
import RoleProtectedRoute from './components/RoleProtectedRoute';
import Home from './components/public/Home';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState('');
  const [userRole, setUserRole] = useState('');
  const [authView, setAuthView] = useState('home'); // 'home' | 'login' | 'register' | 'registerCandidate'

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
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userRole');
    setToken('');
    setUserRole('');
    setIsLoggedIn(false);
  };

  const navigateToRegister = () => setAuthView('register');
  const navigateToRegisterCandidate = () => setAuthView('registerCandidate');
  const navigateToLogin = () => setAuthView('login');
  const navigateToHome = () => setAuthView('home');

  // Render dashboard based on user role
  const renderDashboard = () => {
    switch (userRole) {
      case 'admin':
        return <AdminDashboard token={token} onLogout={() => { handleLogout(); navigateToHome(); }} />;
      case 'voter':
        return <VoterDashboard token={token} onLogout={() => { handleLogout(); navigateToHome(); }} />;
      case 'candidate':
        return <CandidateDashboard token={token} onLogout={() => { handleLogout(); navigateToHome(); }} />;
      default:
        return <Dashboard token={token} userRole={userRole} onLogout={() => { handleLogout(); navigateToHome(); }} />;
    }
  };

  return (
    <div className="App">
      {!isLoggedIn ? (
        authView === 'home' ? (
          <Home onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onRegisterCandidateClick={navigateToRegisterCandidate} />
        ) : authView === 'login' ? (
          <Login onLogin={handleLogin} onNavigateToRegister={navigateToRegister} onNavigateToHome={navigateToHome} />
        ) : (
          authView === 'register' ? (
            <Register onNavigateToLogin={navigateToLogin} onNavigateToCandidate={navigateToRegisterCandidate} />
          ) : (
            <CandidateRegister onNavigateToLogin={navigateToLogin} onNavigateToVoter={navigateToRegister} />
          )
        )
      ) : (
        renderDashboard()
      )}
    </div>
  );
}

export default App;