import React from 'react';
import SiteLayout from '../layout/SiteLayout.jsx';

export default function FAQ({ onLoginClick, onRegisterClick, onNavigateToHome, onNavigateToFAQ, onNavigateToSupport, onNavigateToAccessibility }) {
  return (
    <SiteLayout onLoginClick={onLoginClick} onRegisterClick={onRegisterClick} onNavigateToHome={onNavigateToHome} isLoggedIn={false} onNavigateToFAQ={onNavigateToFAQ} onNavigateToSupport={onNavigateToSupport} onNavigateToAccessibility={onNavigateToAccessibility}>
      <section id="faq" className="eci-info-section">
        <h3>Frequently Asked Questions</h3>
        <div className="eci-faq-content">
          <div className="eci-faq-item">
            <h4>How do I register to vote?</h4>
            <p>Click on the "Register as Voter" button, fill in your personal details, verify your identity through face recognition, and submit your registration. You'll receive a confirmation email once approved.</p>
          </div>
          <div className="eci-faq-item">
            <h4>Is my vote secure and anonymous?</h4>
            <p>Yes, our system uses advanced encryption and blockchain technology to ensure your vote is secure and completely anonymous. Your identity is verified separately from the voting process.</p>
          </div>
          <div className="eci-faq-item">
            <h4>What documents do I need to register?</h4>
            <p>You'll need a valid government-issued ID and access to a camera for face verification. The system will guide you through the verification process step by step.</p>
          </div>
          <div className="eci-faq-item">
            <h4>Can I change my vote after submitting?</h4>
            <p>No, once your vote is submitted, it cannot be changed to maintain the integrity of the election process. Please review your selection carefully before submitting.</p>
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
