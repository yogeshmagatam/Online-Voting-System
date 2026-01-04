import React from 'react';
import SiteLayout from '../layout/SiteLayout';

export default function Mission({ onLoginClick, onRegisterClick, onNavigateToHome, onNavigateToMission, onNavigateToSecurity, onNavigateToPrivacy, onNavigateToFAQ, onNavigateToSupport, onNavigateToAccessibility }) {
  return (
    <SiteLayout onLoginClick={onLoginClick} onRegisterClick={onRegisterClick} onNavigateToHome={onNavigateToHome} isLoggedIn={false} onNavigateToMission={onNavigateToMission} onNavigateToSecurity={onNavigateToSecurity} onNavigateToPrivacy={onNavigateToPrivacy} onNavigateToFAQ={onNavigateToFAQ} onNavigateToSupport={onNavigateToSupport} onNavigateToAccessibility={onNavigateToAccessibility}>
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
    </SiteLayout>
  );
}
