import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Check } from 'lucide-react';
import './Pricing.css';

/**
 * Pricing — displays the three subscription tiers: Free, Pro, and Enterprise.
 */
function Pricing() {
  const navigate = useNavigate();

  const pricingPlans = [
    {
      id: 'free',
      name: 'Free',
      price: '$0',
      billingPeriod: 'forever',
      description: 'Perfect for trying things out and personal projects.',
      features: [
        '5 AI-generated websites per month',
        '3 active projects',
        'Community templates',
        'Basic chat history',
        'Lovable subdomain hosting',
      ],
      unavailableFeatures: [
        'Custom domain',
        'Priority AI generation',
        'Team collaboration',
      ],
      buttonLabel: 'Get Started Free',
      buttonId: 'pricing-free-plan-button',
      isHighlighted: false,
    },
    {
      id: 'pro',
      name: 'Pro',
      price: '$19',
      billingPeriod: 'per month',
      description: 'For makers and developers who build seriously.',
      features: [
        'Unlimited AI-generated websites',
        'Unlimited active projects',
        'All premium templates',
        'Full chat history & context',
        'Custom domain support',
        'Priority AI generation',
        'Export HTML/CSS/JS code',
      ],
      unavailableFeatures: [
        'Team collaboration',
      ],
      buttonLabel: 'Upgrade to Pro',
      buttonId: 'pricing-pro-plan-button',
      isHighlighted: true,
      badge: 'Most Popular',
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: 'Custom',
      billingPeriod: 'contact us',
      description: 'For teams and organizations building at scale.',
      features: [
        'Everything in Pro',
        'Team collaboration',
        'Shared project workspace',
        'SSO / SAML login',
        'Dedicated AI capacity',
        'SLA & priority support',
        'Custom integrations',
      ],
      unavailableFeatures: [],
      buttonLabel: 'Contact Sales',
      buttonId: 'pricing-enterprise-plan-button',
      isHighlighted: false,
    },
  ];

  const handlePlanButtonClick = (planId) => {
    if (planId === 'free') {
      navigate('/auth?mode=register');
    } else if (planId === 'pro') {
      // TODO: Integrate with payment provider (Stripe, etc.)
      navigate('/auth?mode=register');
    } else {
      // Enterprise — link to contact page or email
      window.location.href = 'mailto:sales@lovable-clone.com';
    }
  };

  return (
    <div className="pricing-page">
      {/* ─── Top Bar ─────────────────────────────────────────────── */}
      <div className="pricing-top-bar">
        <button
          id="pricing-back-button"
          className="pricing-back-button"
          onClick={() => navigate(-1)}
        >
          <ArrowLeft size={16} />
          Back
        </button>
        <div className="pricing-top-bar-logo">
          <span>💖</span>
          <span className="pricing-logo-text">Lovable Pricing</span>
        </div>
        <div />
      </div>

      {/* ─── Page Header ─────────────────────────────────────────── */}
      <div className="pricing-page-header">
        <h1 className="pricing-page-title">Simple, honest pricing</h1>
        <p className="pricing-page-subtitle">
          No hidden fees. No credit card required to get started.
        </p>
      </div>

      {/* ─── Pricing Cards ────────────────────────────────────────── */}
      <div className="pricing-cards-container">
        {pricingPlans.map((plan) => (
          <div
            key={plan.id}
            id={`pricing-plan-card-${plan.id}`}
            className={`pricing-plan-card ${plan.isHighlighted ? 'is-highlighted-plan' : ''}`}
          >
            {/* Popular badge */}
            {plan.badge && (
              <div className="pricing-plan-badge">{plan.badge}</div>
            )}

            <div className="pricing-plan-name">{plan.name}</div>
            <div className="pricing-plan-price-row">
              <span className="pricing-plan-price">{plan.price}</span>
              <span className="pricing-plan-billing-period">/ {plan.billingPeriod}</span>
            </div>
            <p className="pricing-plan-description">{plan.description}</p>

            <button
              id={plan.buttonId}
              className={`pricing-plan-button ${plan.isHighlighted ? 'is-primary-button' : 'is-secondary-button'}`}
              onClick={() => handlePlanButtonClick(plan.id)}
            >
              {plan.buttonLabel}
            </button>

            {/* Feature list */}
            <ul className="pricing-features-list">
              {plan.features.map((featureText, index) => (
                <li key={index} className="pricing-feature-item pricing-feature-included">
                  <Check size={14} className="pricing-feature-check-icon" />
                  {featureText}
                </li>
              ))}
              {plan.unavailableFeatures.map((featureText, index) => (
                <li key={index} className="pricing-feature-item pricing-feature-unavailable">
                  <span className="pricing-feature-cross-icon">✕</span>
                  {featureText}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* ─── FAQ / Reassurance Footer ─────────────────────────────── */}
      <div className="pricing-footer-note">
        Questions? Email us at{' '}
        <a href="mailto:hello@lovable-clone.com" className="pricing-footer-email-link">
          hello@lovable-clone.com
        </a>
      </div>
    </div>
  );
}

export default Pricing;
