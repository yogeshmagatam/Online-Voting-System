import React from 'react';
import SiteLayout from '../layout/SiteLayout';

export default function Privacy({ onLoginClick, onRegisterClick, onNavigateToHome, onNavigateToMission, onNavigateToSecurity, onNavigateToPrivacy, onNavigateToFAQ, onNavigateToSupport, onNavigateToAccessibility }) {
  return (
    <SiteLayout onLoginClick={onLoginClick} onRegisterClick={onRegisterClick} onNavigateToHome={onNavigateToHome} isLoggedIn={false} onNavigateToMission={onNavigateToMission} onNavigateToSecurity={onNavigateToSecurity} onNavigateToPrivacy={onNavigateToPrivacy} onNavigateToFAQ={onNavigateToFAQ} onNavigateToSupport={onNavigateToSupport} onNavigateToAccessibility={onNavigateToAccessibility}>
      <section className="eci-info-section">
        <h3>Privacy</h3>
        <div className="eci-about-content">
          <div className="eci-about-item">
            <h4>🔒 Vote Secrecy</h4>
            <p>Your vote is completely anonymous. While your identity is verified during registration, your voting choice is completely separated from your identity and cannot be linked back to you by anyone, including election officials.</p>
          </div>
          <div className="eci-about-item">
            <h4>📁 Data Minimization</h4>
            <p>We collect only the minimum personal information necessary for voter registration and identity verification. We do not sell, share, or rent your personal data to any third parties.</p>
          </div>
          <div className="eci-about-item">
            <h4>🗑️ Data Retention Policy</h4>
            <p>Biometric data used for identity verification is deleted immediately after verification is complete. Your personal information is retained only as long as required by law and then securely destroyed.</p>
          </div>
          <div className="eci-about-item">
            <h4>👁️ Transparency Reports</h4>
            <p>We publish regular transparency reports detailing any data requests from government agencies and how we respond to them. We are committed to being open about government access to user data.</p>
          </div>
          <div className="eci-about-item">
            <h4>📜 Privacy by Design</h4>
            <p>Privacy is built into every aspect of our system. We use techniques like differential privacy, data anonymization, and encryption to protect your information throughout the election process.</p>
          </div>
          <div className="eci-about-item">
            <h4>⚖️ Legal Compliance</h4>
            <p>Our platform complies with all applicable data protection laws and regulations, including GDPR, CCPA, and other privacy legislation. You have the right to access, modify, or delete your personal data.</p>
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
