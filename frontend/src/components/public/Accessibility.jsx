import React from 'react';
import SiteLayout from '../layout/SiteLayout.jsx';

export default function Accessibility({ onLoginClick, onRegisterClick, onNavigateToHome, onNavigateToFAQ, onNavigateToSupport, onNavigateToAccessibility }) {
  return (
    <SiteLayout onLoginClick={onLoginClick} onRegisterClick={onRegisterClick} onNavigateToHome={onNavigateToHome} isLoggedIn={false} onNavigateToFAQ={onNavigateToFAQ} onNavigateToSupport={onNavigateToSupport} onNavigateToAccessibility={onNavigateToAccessibility}>
      <section id="accessibility" className="eci-info-section">
        <h3>Accessibility Features</h3>
        <div className="eci-accessibility-content">
          <div className="eci-accessibility-item">
            <h4>♿ Screen Reader Compatibility</h4>
            <p>Our platform is fully compatible with popular screen readers including JAWS, NVDA, and VoiceOver. All interactive elements have proper ARIA labels for seamless navigation.</p>
          </div>
          <div className="eci-accessibility-item">
            <h4>⌨️ Keyboard Navigation</h4>
            <p>The entire platform can be navigated using only a keyboard. Use Tab to move between elements, Enter to select, and arrow keys for navigation within components.</p>
          </div>
          <div className="eci-accessibility-item">
            <h4>🔍 Text Size & Contrast</h4>
            <p>Use your browser's zoom function (Ctrl/Cmd + Plus/Minus) to adjust text size. Our design meets WCAG 2.1 AA standards for color contrast to ensure readability.</p>
          </div>
          <div className="eci-accessibility-item">
            <h4>🗣️ Alternative Verification Methods</h4>
            <p>If you have difficulty with face verification, please contact our support team for alternative identity verification methods.</p>
          </div>
          <div className="eci-accessibility-item">
            <h4>🌐 Multi-language Support</h4>
            <p>The platform supports multiple languages. Use the language selector in the top menu to choose your preferred language.</p>
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}
