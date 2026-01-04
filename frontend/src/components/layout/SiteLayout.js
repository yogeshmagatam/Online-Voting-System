import React from 'react';

export default function SiteLayout({ children, onLoginClick, onRegisterClick, onLogout, onNavigateToHome, isLoggedIn, onNavigateToMission, onNavigateToSecurity, onNavigateToPrivacy, onNavigateToFAQ, onNavigateToSupport, onNavigateToAccessibility }) {
  return (
    <div className="eci-page">
      <header className="eci-header">
        <div className="eci-topbar">
          <div className="eci-topbar-left">Election System</div>
          <div className="eci-topbar-right">
            {isLoggedIn ? (
              <button className="eci-link" onClick={onLogout}>Logout</button>
            ) : (
              <>
                <button className="eci-link eci-link-animated" onClick={onLoginClick}>Login</button>
                <button className="eci-link eci-link-animated" onClick={onRegisterClick}>Register</button>
              </>
            )}
          </div>
        </div>
        <div className="eci-brand">
          <div className="eci-logo" aria-hidden>
            <img src="/ECOI-project.jpg" alt="Portal logo" className="eci-logo-img-square" />
          </div>
          <div className="eci-title">
            <h1>Secure Election Portal</h1>
            <p>Transparent • Accessible • Secure</p>
          </div>
        </div>
        <nav className="eci-nav" aria-label="primary">
          <ul>
            <li><a href="#services" className="eci-nav-link">Services</a></li>
            <li><a href="#contact">Contact</a></li>
          </ul>
        </nav>
      </header>

      <main>
        {children}
      </main>

      <footer className="eci-footer" id="contact">
        <div className="eci-footer-grid">
          <div>
            <h4>About</h4>
            <ul>
              <li><button className="eci-link" onClick={onNavigateToMission} style={{background: 'none', border: 'none', padding: 0, color: '#c7d2e2', cursor: 'pointer', textDecoration: 'none'}}>Our mission</button></li>
              <li><button className="eci-link" onClick={onNavigateToSecurity} style={{background: 'none', border: 'none', padding: 0, color: '#c7d2e2', cursor: 'pointer', textDecoration: 'none'}}>Security</button></li>
              <li><button className="eci-link" onClick={onNavigateToPrivacy} style={{background: 'none', border: 'none', padding: 0, color: '#c7d2e2', cursor: 'pointer', textDecoration: 'none'}}>Privacy</button></li>
            </ul>
          </div>
          <div>
            <h4>Help</h4>
            <ul>
              <li><button className="eci-link" onClick={onNavigateToFAQ} style={{background: 'none', border: 'none', padding: 0, color: '#c7d2e2', cursor: 'pointer', textDecoration: 'none'}}>FAQ</button></li>
              <li><button className="eci-link" onClick={onNavigateToSupport} style={{background: 'none', border: 'none', padding: 0, color: '#c7d2e2', cursor: 'pointer', textDecoration: 'none'}}>Support</button></li>
              <li><button className="eci-link" onClick={onNavigateToAccessibility} style={{background: 'none', border: 'none', padding: 0, color: '#c7d2e2', cursor: 'pointer', textDecoration: 'none'}}>Accessibility</button></li>
            </ul>
          </div>
          <div>
            <h4>Contact</h4>
            <ul>
              <li>Email: akashgupta1641@gmail.com</li>
              <li>Phone: +91 8685497320</li>
            </ul>
          </div>
        </div>
        <div className="eci-footer-bottom">© {new Date().getFullYear()} Secure Election Portal</div>
      </footer>
    </div>
  );
}
