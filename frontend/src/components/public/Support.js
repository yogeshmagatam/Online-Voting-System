import React from 'react';
import SiteLayout from '../layout/SiteLayout';

export default function Support({ onLoginClick, onRegisterClick, onNavigateToHome, onNavigateToFAQ, onNavigateToSupport, onNavigateToAccessibility }) {
  return (
    <SiteLayout onLoginClick={onLoginClick} onRegisterClick={onRegisterClick} onNavigateToHome={onNavigateToHome} isLoggedIn={false} onNavigateToFAQ={onNavigateToFAQ} onNavigateToSupport={onNavigateToSupport} onNavigateToAccessibility={onNavigateToAccessibility}>
      <section id="support" className="eci-info-section">
        <h3>Support & Help</h3>
        <div className="eci-support-content">
          <div className="eci-support-item">
            <h4>📧 Email Support</h4>
            <p>For general inquiries and support, contact us at: <strong>akashgupta1641@gmail.com</strong></p>
            <p>Response time: Within 24-48 hours</p>
          </div>
          <div className="eci-support-item">
            <h4>📞 Phone Support</h4>
            <p>Call us at: <strong>+91 8685497320</strong></p>
            <p>Available: Monday to Friday, 9:00 AM - 6:00 PM IST</p>
          </div>
          <div className="eci-support-item">
            <h4>🔧 Technical Issues</h4>
            <p>If you're experiencing technical difficulties with registration, login, or voting, please clear your browser cache and try again. If the problem persists, contact our support team with a detailed description of the issue.</p>
          </div>
          <div className="eci-support-item">
            <h4>🛡️ Report Security Concerns</h4>
            <p>If you notice any suspicious activity or security vulnerabilities, please report them immediately to our security team at the contact information above.</p>
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
