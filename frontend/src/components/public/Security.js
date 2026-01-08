import React from 'react';
import SiteLayout from '../layout/SiteLayout';

export default function Security({ onLoginClick, onRegisterClick, onNavigateToHome, onNavigateToMission, onNavigateToSecurity, onNavigateToPrivacy, onNavigateToFAQ, onNavigateToSupport, onNavigateToAccessibility }) {
  return (
    <SiteLayout onLoginClick={onLoginClick} onRegisterClick={onRegisterClick} onNavigateToHome={onNavigateToHome} isLoggedIn={false} onNavigateToMission={onNavigateToMission} onNavigateToSecurity={onNavigateToSecurity} onNavigateToPrivacy={onNavigateToPrivacy} onNavigateToFAQ={onNavigateToFAQ} onNavigateToSupport={onNavigateToSupport} onNavigateToAccessibility={onNavigateToAccessibility}>
      <section className="eci-info-section">
        <h3>Security</h3>
        <div className="eci-about-content">
          <div className="eci-about-item">
            <h4>🔐 End-to-End Encryption</h4>
            <p>All data transmitted between your device and our servers is encrypted using industry-standard SSL/TLS encryption. Your personal information and voting choices are protected with military-grade encryption algorithms.</p>
          </div>
          <div className="eci-about-item">
            <h4>⛓️ Blockchain Technology</h4>
            <p>We utilize blockchain technology to ensure the immutability and transparency of election records. Each vote is cryptographically hashed and stored in a distributed ledger, making it impossible to alter without detection.</p>
          </div>
          <div className="eci-about-item">
            <h4>🧬 Biometric Verification</h4>
            <p>Face recognition technology is used for identity verification to prevent impersonation and fraud. The biometric data is processed securely and not stored on our servers, ensuring your privacy.</p>
          </div>
          <div className="eci-about-item">
            <h4>🛡️ Regular Security Audits</h4>
            <p>We conduct regular security audits and penetration testing by independent third-party security firms to identify and address any vulnerabilities. Our system is continuously monitored for threats.</p>
          </div>
          <div className="eci-about-item">
            <h4>🔑 Multi-Factor Authentication</h4>
            <p>User accounts are protected with multi-factor authentication including password, email verification, and OTP. This ensures that only authorized users can access their accounts.</p>
          </div>
          <div className="eci-about-item">
            <h4>📋 Audit Trails</h4>
            <p>All system activities are logged and can be audited. Election officials can verify the integrity of the entire voting process from registration to vote counting.</p>
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
