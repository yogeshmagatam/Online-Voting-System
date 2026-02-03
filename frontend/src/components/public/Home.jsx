import React from 'react';
import SiteLayout from '../layout/SiteLayout.jsx';

const Hero = ({ onRegisterClick }) => (
  <section className="eci-hero">
    <div className="eci-hero-content">
      <h2>Empowering Every Voter</h2>
      <p>Register, verify your identity, and cast your vote securely.</p>
    </div>
  </section>
);

const QuickLinks = ({ onLoginClick, onRegisterClick, onRegisterAdminClick }) => (
  <section id="services" className="eci-quicklinks">
    <h3>Services</h3>
    <div className="eci-buttons-wrapper">
      <button className="btn-action-animated" onClick={onRegisterClick}>
        <span className="btn-action-icon">📝</span>
        <span className="btn-action-text">Register as Voter</span>
      </button>
      <button className="btn-action-animated" onClick={onLoginClick}>
        <span className="btn-action-icon">🔐</span>
        <span className="btn-action-text">Login</span>
      </button>
      <button className="btn-action-animated" onClick={onRegisterAdminClick}>
        <span className="btn-action-icon">🛡️</span>
        <span className="btn-action-text">Register as Admin</span>
      </button>
    </div>
  </section>
);

export default function Home({ onLoginClick, onRegisterClick, onRegisterAdminClick, onNavigateToHome, onNavigateToMission, onNavigateToSecurity, onNavigateToPrivacy, onNavigateToFAQ, onNavigateToSupport, onNavigateToAccessibility }) {
  return (
    <SiteLayout onLoginClick={onLoginClick} onRegisterClick={onRegisterClick} onNavigateToHome={onNavigateToHome} isLoggedIn={false} onNavigateToMission={onNavigateToMission} onNavigateToSecurity={onNavigateToSecurity} onNavigateToPrivacy={onNavigateToPrivacy} onNavigateToFAQ={onNavigateToFAQ} onNavigateToSupport={onNavigateToSupport} onNavigateToAccessibility={onNavigateToAccessibility}>
      <Hero onRegisterClick={onRegisterClick} />
      <QuickLinks onLoginClick={onLoginClick} onRegisterClick={onRegisterClick} onRegisterAdminClick={onRegisterAdminClick} />
    </SiteLayout>
  );
}
