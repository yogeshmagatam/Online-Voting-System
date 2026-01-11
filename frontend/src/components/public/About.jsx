import React from 'react';
import SiteLayout from '../layout/SiteLayout.jsx';

export default function About({ onLoginClick, onRegisterClick, onNavigateToAbout, onNavigateToFAQ, onNavigateToSupport, onNavigateToAccessibility }) {
  return (
    <SiteLayout onLoginClick={onLoginClick} onRegisterClick={onRegisterClick} isLoggedIn={false} onNavigateToAbout={onNavigateToAbout} onNavigateToFAQ={onNavigateToFAQ} onNavigateToSupport={onNavigateToSupport} onNavigateToAccessibility={onNavigateToAccessibility}>
      <section className="eci-info-section">
        <h3>Our Mission</h3>
        <div className="eci-about-content">
          <div className="eci-about-item">
            <h4>🎯 Empowering Democratic Participation</h4>
            <p>Our mission is to create a secure, transparent, and accessible digital election platform that empowers every citizen to participate in the democratic process with confidence. We believe that voting should be easy, secure, and trustworthy for everyone.</p>
          </div>
          <div className="eci-about-item">
            <h4>🌍 Commitment to Integrity</h4>
            <p>We are committed to maintaining the highest standards of election integrity and security. Our platform is designed to prevent fraud, ensure accuracy, and protect the privacy of every voter while maintaining full transparency and auditability.</p>
          </div>
          <div className="eci-about-item">
            <h4>♿ Inclusive Access</h4>
            <p>We believe democracy is for everyone. Our platform is designed to be fully accessible to people with disabilities, supports multiple languages, and provides alternative verification methods to ensure no one is left behind.</p>
          </div>
          <div className="eci-about-item">
            <h4>🔄 Continuous Innovation</h4>
            <p>We continuously improve our platform with the latest security technologies and user experience enhancements. Your feedback helps us build a better election system for everyone.</p>
          </div>
        </div>
      </section>

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
