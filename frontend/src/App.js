import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './components/Login';
import Register from './components/Register';
import RegisterAdmin from './components/RegisterAdmin';
import Dashboard from './components/Dashboard';
import AdminDashboard from './components/AdminDashboard';
import VoterDashboard from './components/VoterDashboard';
import RoleProtectedRoute from './components/RoleProtectedRoute';
import Home from './components/public/Home';
import Mission from './components/public/Mission';
import Security from './components/public/Security';
import Privacy from './components/public/Privacy';
import FAQ from './components/public/FAQ';
import Support from './components/public/Support';
import Accessibility from './components/public/Accessibility';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState('');
  const [userRole, setUserRole] = useState('');
  const [authView, setAuthView] = useState('home'); // 'home' | 'login' | 'register' | 'registerAdmin' | 'mission' | 'security' | 'privacy' | 'faq' | 'support' | 'accessibility'

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedRole = localStorage.getItem('userRole');
    if (storedToken) {
      setToken(storedToken);
      setUserRole(storedRole);
      setIsLoggedIn(true);
    }

    // Initialize URL based on current view
    const currentPath = window.location.pathname;
    if (currentPath !== '/' && currentPath !== '') {
      const view = currentPath.substring(1);
      if (view) setAuthView(view);
    }

    // Listen to browser back/forward buttons
    const handlePopState = (event) => {
      const view = event.state?.view || 'home';
      setAuthView(view);
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleLogin = (token, role) => {
    localStorage.setItem('token', token);
    localStorage.setItem('userRole', role);
    setToken(token);
    setUserRole(role);
    setIsLoggedIn(true);
    setAuthView('dashboard'); // Redirect to dashboard after login
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userRole');
    setToken('');
    setUserRole('');
    setIsLoggedIn(false);
  };

  const navigateToRegister = () => {
    setAuthView('register');
    window.history.pushState({ view: 'register' }, '', '/register');
  };
  const navigateToRegisterAdmin = () => {
    setAuthView('registerAdmin');
    window.history.pushState({ view: 'registerAdmin' }, '', '/registerAdmin');
  };
  const navigateToLogin = () => {
    setAuthView('login');
    window.history.pushState({ view: 'login' }, '', '/login');
  };
  const navigateToHome = () => {
    setAuthView('home');
    window.history.pushState({ view: 'home' }, '', '/');
  };
  const navigateToMission = () => {
    setAuthView('mission');
    window.history.pushState({ view: 'mission' }, '', '/mission');
  };
  const navigateToSecurity = () => {
    setAuthView('security');
    window.history.pushState({ view: 'security' }, '', '/security');
  };
  const navigateToPrivacy = () => {
    setAuthView('privacy');
    window.history.pushState({ view: 'privacy' }, '', '/privacy');
  };
  const navigateToFAQ = () => {
    setAuthView('faq');
    window.history.pushState({ view: 'faq' }, '', '/faq');
  };
  const navigateToSupport = () => {
    setAuthView('support');
    window.history.pushState({ view: 'support' }, '', '/support');
  };
  const navigateToAccessibility = () => {
    setAuthView('accessibility');
    window.history.pushState({ view: 'accessibility' }, '', '/accessibility');
  };

  // Render dashboard based on user role
  const renderDashboard = () => {
    switch (userRole) {
      case 'admin':
        return <AdminDashboard token={token} onLogout={() => { handleLogout(); navigateToHome(); }} />;
      case 'voter':
        return <VoterDashboard token={token} onLogout={() => { handleLogout(); navigateToHome(); }} />;
      default:
        return <Dashboard token={token} userRole={userRole} onLogout={() => { handleLogout(); navigateToHome(); }} />;
    }
  };

  return (
    <div className="App">
      {!isLoggedIn ? (
        authView === 'home' ? (
          <Home onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onRegisterAdminClick={navigateToRegisterAdmin} onNavigateToHome={navigateToHome} onNavigateToMission={navigateToMission} onNavigateToSecurity={navigateToSecurity} onNavigateToPrivacy={navigateToPrivacy} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />
        ) : authView === 'login' ? (
          <Login onLogin={handleLogin} onNavigateToRegister={navigateToRegister} onNavigateToHome={navigateToHome} />
        ) : authView === 'registerAdmin' ? (
          <RegisterAdmin onNavigateToLogin={navigateToLogin} />
        ) : authView === 'mission' ? (
          <Mission onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToMission={navigateToMission} onNavigateToSecurity={navigateToSecurity} onNavigateToPrivacy={navigateToPrivacy} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />
        ) : authView === 'security' ? (
          <Security onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToMission={navigateToMission} onNavigateToSecurity={navigateToSecurity} onNavigateToPrivacy={navigateToPrivacy} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />
        ) : authView === 'privacy' ? (
          <Privacy onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToMission={navigateToMission} onNavigateToSecurity={navigateToSecurity} onNavigateToPrivacy={navigateToPrivacy} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />
        ) : authView === 'faq' ? (
          <FAQ onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />
        ) : authView === 'support' ? (
          <Support onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />
        ) : authView === 'accessibility' ? (
          <Accessibility onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} onNavigateToHome={navigateToHome} onNavigateToFAQ={navigateToFAQ} onNavigateToSupport={navigateToSupport} onNavigateToAccessibility={navigateToAccessibility} />
        ) : authView === 'register' ? (
          <Register onNavigateToLogin={navigateToLogin} />
        ) : null
      ) : (
        renderDashboard()
      )}
    </div>
  );
}

export default App;