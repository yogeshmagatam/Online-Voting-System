import React from 'react';

export default function SiteLayout({ children, onLoginClick, onRegisterClick, onLogout, isLoggedIn }) {
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
                <button className="eci-link" onClick={onLoginClick}>Login</button>
                <button className="eci-link" onClick={onRegisterClick}>Register</button>
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
          <div className="eci-search">
            <input type="search" placeholder="Search..." aria-label="Search" />
          </div>
        </div>
        <nav className="eci-nav" aria-label="primary">
          <ul>
            <li><a href="#services">Services</a></li>
            <li><a href="#voter">Voter Info</a></li>
            <li><a href="#results">Results</a></li>
            <li><a href="#resources">Resources</a></li>
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
              <li><a href="#learn">Our mission</a></li>
              <li><a href="#security">Security</a></li>
              <li><a href="#privacy">Privacy</a></li>
            </ul>
          </div>
          <div>
            <h4>Help</h4>
            <ul>
              <li><a href="#faq">FAQ</a></li>
              <li><a href="#support">Support</a></li>
              <li><a href="#accessibility">Accessibility</a></li>
            </ul>
          </div>
          <div>
            <h4>Contact</h4>
            <ul>
              <li>Email: support@example.com</li>
              <li>Phone: +1-555-123-4567</li>
            </ul>
          </div>
        </div>
        <div className="eci-footer-bottom">© {new Date().getFullYear()} Secure Election Portal</div>
      </footer>
    </div>
  );
}
