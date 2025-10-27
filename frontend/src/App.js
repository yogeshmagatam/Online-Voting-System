import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import Home from './components/public/Home';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState('');
  const [userRole, setUserRole] = useState('');
  const [authView, setAuthView] = useState('home'); // 'home' | 'login' | 'register'

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
  const navigateToLogin = () => setAuthView('login');
  const navigateToHome = () => setAuthView('home');

  return (
    <div className="App">
      {!isLoggedIn ? (
        authView === 'home' ? (
          <Home onLoginClick={navigateToLogin} onRegisterClick={navigateToRegister} />
        ) : authView === 'login' ? (
          <Login onLogin={handleLogin} onNavigateToRegister={navigateToRegister} onNavigateToHome={navigateToHome} />
        ) : (
          <Register onNavigateToLogin={navigateToLogin} />
        )
      ) : (
        <Dashboard token={token} userRole={userRole} onLogout={() => { handleLogout(); navigateToHome(); }} />
      )}
    </div>
  );
}

export default App;