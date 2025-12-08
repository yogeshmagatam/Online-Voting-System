import React from 'react';
import SiteLayout from '../layout/SiteLayout';

const Hero = ({ onRegisterClick, onRegisterCandidateClick }) => (
  <section className="eci-hero">
    <div className="eci-hero-content">
      <h2>Empowering Every Voter</h2>
      <p>Register, verify your identity, and cast your vote securely.</p>
      <div className="eci-hero-actions">
        <button className="btn btn-primary" onClick={onRegisterClick}>Register as Voter</button>
        <button className="btn" onClick={onRegisterCandidateClick}>Register as Candidate</button>
        <a className="btn btn-outline" href="#learn">Learn More</a>
      </div>
    </div>
  </section>
);

const QuickLinks = ({ onLoginClick, onRegisterClick, onRegisterCandidateClick }) => (
  <section id="services" className="eci-quicklinks">
    <h3>Quick Links</h3>
    <div className="eci-grid">
      <a className="eci-card" onClick={onRegisterClick} href="#register" role="button">
        <div className="eci-card-icon">📝</div>
        <div className="eci-card-title">Register as Voter</div>
        <div className="eci-card-desc">Create your secure account</div>
      </a>
      <a className="eci-card" onClick={onRegisterCandidateClick} href="#register-candidate" role="button">
        <div className="eci-card-icon">🏛️</div>
        <div className="eci-card-title">Register as Candidate</div>
        <div className="eci-card-desc">Create your candidate profile</div>
      </a>
      <a className="eci-card" onClick={onLoginClick} href="#login" role="button">
        <div className="eci-card-icon">🔐</div>
        <div className="eci-card-title">Login</div>
        <div className="eci-card-desc">Access your dashboard</div>
      </a>
      <a className="eci-card" href="#verify">
        <div className="eci-card-icon">🧑🏻‍💻</div>
        <div className="eci-card-title">Identity Verification</div>
        <div className="eci-card-desc">Secure face verification</div>
      </a>
      <a className="eci-card" href="#results">
        <div className="eci-card-icon">📊</div>
        <div className="eci-card-title">Statistics</div>
        <div className="eci-card-desc">Turnout & analysis</div>
      </a>
    </div>
  </section>
);

const Updates = () => (
  <section id="updates" className="eci-updates">
    <div className="eci-updates-header">
      <h3>Announcements</h3>
      <a href="#all" className="eci-link">View all</a>
    </div>
    <ul className="eci-list">
      <li>System maintenance scheduled for Sunday 02:00–03:00 UTC</li>
      <li>New accessibility enhancements in verification flow</li>
      <li>Security update: rate-limiting protections increased</li>
    </ul>
  </section>
);

const Footer = () => null; // Footer is now provided by SiteLayout

export default function Home({ onLoginClick, onRegisterClick, onRegisterCandidateClick }) {
  return (
    <SiteLayout onLoginClick={onLoginClick} onRegisterClick={onRegisterClick} isLoggedIn={false}>
      <Hero onRegisterClick={onRegisterClick} onRegisterCandidateClick={onRegisterCandidateClick} />
      <QuickLinks onLoginClick={onLoginClick} onRegisterClick={onRegisterClick} onRegisterCandidateClick={onRegisterCandidateClick} />
      <Updates />
    </SiteLayout>
  );
}
