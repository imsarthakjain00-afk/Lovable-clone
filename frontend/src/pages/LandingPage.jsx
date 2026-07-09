import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { LiquidMetalButton } from '../components/ui/liquid-metal-button';
import productDescribe from '../assets/product-describe.png';
import productGenerate from '../assets/product-generate.png';
import productRefine from '../assets/product-refine.png';
import './LandingPage.css';

/**
 * LandingPage — dark editorial / neo-industrial redesign.
 * Typography-led. Liquid Metal as the primary material language.
 * Three editorial storytelling sections: DESCRIBE / GENERATE / REFINE.
 */
function LandingPage() {
  const navigate = useNavigate();
  const heroRef = useRef(null);

  useEffect(() => {
    const el = heroRef.current;
    if (el) {
      requestAnimationFrame(() => el.classList.add('lp-hero--visible'));
    }
  }, []);

  const handleGoToSignUp = () => navigate('/auth?mode=register');
  const handleGoToSignIn = () => navigate('/auth?mode=login');

  return (
    <div className="lp-root">

      {/* ── Navbar ────────────────────────────────────────────────── */}
      <nav className="lp-nav" aria-label="Main navigation">
        {/* Left: Logo */}
        <button
          className="lp-logo"
          onClick={() => navigate('/')}
          aria-label="Lovable home"
        >
          <span className="lp-logo-mark" aria-hidden="true">✦</span>
          <span className="lp-logo-text">Lovable</span>
        </button>

        {/* Center: Nav links */}
        <div className="lp-nav-links" role="list">
          <button
            role="listitem"
            className="lp-nav-link"
            onClick={() => navigate('/templates')}
          >
            Templates
          </button>
          <button
            role="listitem"
            className="lp-nav-link"
            onClick={() => navigate('/pricing')}
          >
            Pricing
          </button>
        </div>

        {/* Right: Actions */}
        <div className="lp-nav-actions">
          <button
            className="lp-nav-signin"
            onClick={handleGoToSignIn}
            aria-label="Sign In"
          >
            Sign In
          </button>
          <LiquidMetalButton
            label="Get Started Free"
            onClick={handleGoToSignUp}
          />
        </div>
      </nav>

      {/* ── Hero: Editorial Manifesto Cover ───────────────────── */}
      <section className="lp-hero" aria-labelledby="hero-heading">
        <div className="lp-hero-top-rule" aria-hidden="true" />

        {/* Main manifesto canvas */}
        <div ref={heroRef} className="lp-hero-manifesto">

          {/* Metadata row — top of canvas */}
          <div className="lp-hero-meta" aria-label="Product classification">
            <span className="lp-hero-meta-item">✦ LOVABLE</span>
            <span className="lp-hero-meta-sep" aria-hidden="true">/</span>
            <span className="lp-hero-meta-item">AI WEBSITE SYSTEM</span>
            <span className="lp-hero-meta-sep" aria-hidden="true">/</span>
            <span className="lp-hero-meta-item">2026</span>
          </div>

          {/* Statement Block 1 — anchored left */}
          <div className="lp-hero-statement-top" aria-hidden="true">
            <span className="lp-hero-word-primary">Intent</span>
            <span className="lp-hero-word-comma">,</span>
          </div>

          {/* CTA — sits in the visual space between the two phrases */}
          <div className="lp-hero-cta-zone">
            <LiquidMetalButton
              label="Start Building for Free"
              onClick={handleGoToSignUp}
            />
          </div>

          {/* Statement Block 2 — anchored right */}
          <div className="lp-hero-statement-bottom" aria-hidden="true">
            <span className="lp-hero-word-secondary">not syntax.</span>
          </div>

          {/* Invisible accessible headline for screen readers */}
          <h1 id="hero-heading" className="lp-hero-accessible-title">
            Intent, not syntax. — Lovable: AI Website Builder
          </h1>
        </div>

        {/* Bottom editorial index line */}
        <div className="lp-hero-index-bar" aria-hidden="true">
          <div className="lp-hero-rule" />
          <div className="lp-hero-index-inner">
            <span className="lp-hero-index-left">LOVABLE / PRODUCT SYSTEM 001</span>
            <span className="lp-hero-index-center">AI WEBSITE BUILDER</span>
            <span className="lp-hero-index-right">SCROLL TO EXPLORE ↓</span>
          </div>
        </div>
      </section>


      {/* ── 01 / DESCRIBE ─────────────────────────────────────────── */}
      <section
        className="lp-editorial lp-editorial--normal"
        aria-labelledby="section-describe-heading"
      >
        <div className="lp-section-rule" aria-hidden="true" />
        <div className="lp-editorial-inner">
          {/* Text column */}
          <div className="lp-editorial-text">
            <div className="lp-section-label" aria-label="Section 01: Describe">
              <span className="lp-section-num">01</span>
              <span className="lp-section-label-divider" aria-hidden="true">/</span>
              <span>DESCRIBE</span>
            </div>
            <h2 id="section-describe-heading" className="lp-editorial-title">
              Tell Lovable what
              <br />
              you want to build.
            </h2>
            <p className="lp-editorial-body">
              No syntax.
              <br />
              No setup.
              <br />
              Just an idea.
            </p>
          </div>

          {/* Visual column */}
          <div className="lp-editorial-visual">
            <div className="lp-visual-frame" aria-hidden="true">
              <img
                src={productDescribe}
                alt="Lovable prompt interface — type a description and watch your site take shape"
                className="lp-visual-img"
                loading="lazy"
              />
            </div>
          </div>
        </div>
        <div className="lp-section-rule" aria-hidden="true" />
      </section>

      {/* ── 02 / GENERATE ─────────────────────────────────────────── */}
      <section
        className="lp-editorial lp-editorial--reverse"
        aria-labelledby="section-generate-heading"
      >
        <div className="lp-editorial-inner">
          {/* Visual column (left on desktop) */}
          <div className="lp-editorial-visual">
            <div className="lp-visual-frame" aria-hidden="true">
              <img
                src={productGenerate}
                alt="Lovable generation interface — real-time code and live preview side by side"
                className="lp-visual-img"
                loading="lazy"
              />
            </div>
          </div>

          {/* Text column (right on desktop) */}
          <div className="lp-editorial-text">
            <div className="lp-section-label" aria-label="Section 02: Generate">
              <span className="lp-section-num">02</span>
              <span className="lp-section-label-divider" aria-hidden="true">/</span>
              <span>GENERATE</span>
            </div>
            <h2 id="section-generate-heading" className="lp-editorial-title">
              Watch it become
              <br />
              a real product.
            </h2>
            <p className="lp-editorial-body">
              Full HTML, CSS and JavaScript.
              <br />
              Real code. Live preview.
              <br />
              Seconds, not hours.
            </p>
          </div>
        </div>
        <div className="lp-section-rule" aria-hidden="true" />
      </section>

      {/* ── 03 / REFINE ───────────────────────────────────────────── */}
      <section
        className="lp-editorial lp-editorial--normal"
        aria-labelledby="section-refine-heading"
      >
        <div className="lp-editorial-inner">
          {/* Text column */}
          <div className="lp-editorial-text">
            <div className="lp-section-label" aria-label="Section 03: Refine">
              <span className="lp-section-num">03</span>
              <span className="lp-section-label-divider" aria-hidden="true">/</span>
              <span>REFINE</span>
            </div>
            <h2 id="section-refine-heading" className="lp-editorial-title">
              Change anything.
              <br />
              Keep building.
            </h2>
            <p className="lp-editorial-body">
              Every conversation builds
              <br />
              on the last. Iterate naturally —
              <br />
              no context lost.
            </p>
          </div>

          {/* Visual column */}
          <div className="lp-editorial-visual">
            <div className="lp-visual-frame" aria-hidden="true">
              <img
                src={productRefine}
                alt="Lovable chat refinement — continue the conversation to perfect your site"
                className="lp-visual-img"
                loading="lazy"
              />
            </div>
          </div>
        </div>
        <div className="lp-section-rule" aria-hidden="true" />
      </section>

      {/* ── Final CTA ─────────────────────────────────────────────── */}
      <section className="lp-final-cta" aria-labelledby="final-cta-heading">
        <div className="lp-final-cta-inner">
          <p className="lp-final-cta-overline">
            <span className="lp-final-cta-overline-mark" aria-hidden="true">✦</span>
            &nbsp;LOVABLE / AI WEBSITE SYSTEM
          </p>
          <h2 id="final-cta-heading" className="lp-final-cta-title">
            Start building
            <br />
            something real.
          </h2>
          <div className="lp-final-cta-action">
            <LiquidMetalButton
              label="Get Started — It's Free"
              onClick={handleGoToSignUp}
            />
          </div>
        </div>
        <div className="lp-section-rule" aria-hidden="true" />
      </section>

      {/* ── Footer ────────────────────────────────────────────────── */}
      <footer className="lp-footer" role="contentinfo">
        <div className="lp-footer-inner">
          <div className="lp-footer-brand">
            <span className="lp-logo-mark" aria-hidden="true">✦</span>
            <span className="lp-footer-brand-text">Lovable</span>
          </div>
          <nav className="lp-footer-links" aria-label="Footer navigation">
            <button className="lp-footer-link" onClick={() => navigate('/templates')}>Templates</button>
            <button className="lp-footer-link" onClick={() => navigate('/pricing')}>Pricing</button>
            <button className="lp-footer-link" onClick={handleGoToSignIn}>Sign In</button>
          </nav>
          <p className="lp-footer-copy">© 2026 Lovable</p>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
