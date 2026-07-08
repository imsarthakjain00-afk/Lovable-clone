import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { LiquidMetalButton } from '../components/ui/liquid-metal-button';
import './LandingPage.css';

/**
 * LandingPage — the first screen users see.
 * Contains the hero section, feature highlights, and Sign Up / Sign In buttons.
 */
function LandingPage() {
  const navigate = useNavigate();
  const heroTitleRef = useRef(null);

  // Animate the hero title characters on mount
  useEffect(() => {
    const titleElement = heroTitleRef.current;
    if (titleElement) {
      titleElement.classList.add('is-visible');
    }
  }, []);

  const handleGoToSignUp = () => navigate('/auth?mode=register');
  const handleGoToSignIn = () => navigate('/auth?mode=login');

  const featureList = [
    {
      icon: '🤖',
      title: 'AI Code Generation',
      description: 'Describe your website in plain English and our AI writes every line of code for you.',
    },
    {
      icon: '🚀',
      title: 'One-Click Deployment',
      description: 'Your website goes live instantly. No servers, no configuration, no hassle.',
    },
    {
      icon: '💬',
      title: 'Chat to Refine',
      description: 'Keep chatting to iterate and improve. Every prompt builds on the last.',
    },
    {
      icon: '📦',
      title: 'Website Templates',
      description: 'Start from a curated template and customize with natural language.',
    },
    {
      icon: '📜',
      title: 'Full Chat History',
      description: 'Every project saves your full conversation so you can pick up right where you left off.',
    },
    {
      icon: '💳',
      title: 'Simple Pricing',
      description: 'A free tier to get started, and pro plans that scale with your needs.',
    },
  ];

  return (
    <div className="landing-page">
      {/* ─── Top Navbar ─────────────────────────────────────────────── */}
      <nav className="landing-navbar">
        <div className="landing-navbar-logo">
          <span className="landing-logo-icon">💖</span>
          <span className="landing-logo-text">Lovable</span>
        </div>
        <div className="landing-navbar-links">
          <span onClick={() => navigate('/templates')}>Templates</span>
          <span onClick={() => navigate('/pricing')}>Pricing</span>
        </div>
        <div className="landing-navbar-buttons" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <LiquidMetalButton
            label="Sign In"
            onClick={handleGoToSignIn}
            viewMode="text"
            width={90}
          />
          <LiquidMetalButton
            label="Get Started Free"
            onClick={handleGoToSignUp}
          />
        </div>
      </nav>

      {/* ─── Hero Section ────────────────────────────────────────────── */}
      <section className="landing-hero-section">
        <div className="landing-hero-badge">✨ AI-Powered Website Builder</div>
        <h1
          ref={heroTitleRef}
          className="landing-hero-title"
        >
          Build any website
          <br />
          <span className="landing-hero-title-gradient">with one prompt</span>
        </h1>
        <p className="landing-hero-subtitle">
          No code. No designers. No waiting.
          <br />
          Just describe what you want and Lovable builds it for you.
        </p>
        <div className="landing-hero-buttons" style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap', justifyContent: 'center' }}>
          <LiquidMetalButton
            label="Start Building for Free"
            onClick={handleGoToSignUp}
          />
          <LiquidMetalButton
            label="Browse Templates"
            onClick={() => navigate('/templates')}
            width={170}
          />
        </div>

        {/* Fake prompt preview to show what the product does */}
        <div className="landing-demo-prompt-card">
          <div className="landing-demo-prompt-label">Try something like...</div>
          <div className="landing-demo-prompt-text">
            "Create a modern SaaS landing page for a project management tool
            with a dark theme, feature highlights, and a pricing section."
          </div>
          <div className="landing-demo-prompt-arrow">→ Generates a full website in seconds</div>
        </div>
      </section>

      {/* ─── Features Grid ───────────────────────────────────────────── */}
      <section className="landing-features-section">
        <h2 className="landing-features-heading">Everything you need to build fast</h2>
        <div className="landing-features-grid">
          {featureList.map((feature, index) => (
            <div
              key={index}
              className="landing-feature-card"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <span className="landing-feature-icon">{feature.icon}</span>
              <h3 className="landing-feature-title">{feature.title}</h3>
              <p className="landing-feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Bottom CTA Banner ───────────────────────────────────────── */}
      <section className="landing-cta-section">
        <h2 className="landing-cta-title">Ready to build something lovable?</h2>
        <p className="landing-cta-subtitle">
          Join thousands of makers who ship websites in minutes, not months.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
          <LiquidMetalButton
            label="Get Started — It's Free"
            onClick={handleGoToSignUp}
          />
        </div>
      </section>

      {/* ─── Footer ──────────────────────────────────────────────────── */}
      <footer className="landing-footer">
        <span className="landing-logo-icon">💖</span>
        <span>Lovable Clone © 2026</span>
      </footer>
    </div>
  );
}

export default LandingPage;
