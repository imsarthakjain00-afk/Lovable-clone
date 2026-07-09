import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authAPI } from '../api';
import { signInWithPopup } from 'firebase/auth';
import { auth, googleProvider } from '../firebase';
import './AuthPage.css';

/**
 * AuthPage — split-panel premium auth design.
 * Left: editorial brand panel (hidden on mobile).
 * Right: focused form panel.
 */
function AuthPage({ onLoginSuccess }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [authMode, setAuthMode] = useState(
    searchParams.get('mode') === 'register' ? 'register' : 'login'
  );

  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const modeFromUrl = searchParams.get('mode');
    setAuthMode(modeFromUrl === 'register' ? 'register' : 'login');
  }, [searchParams]);

  const clearFormFields = () => {
    setFullName(''); setUsername(''); setEmail('');
    setMobileNumber(''); setPassword('');
    setErrorMessage(''); setSuccessMessage('');
  };

  const switchToLoginMode = () => {
    clearFormFields();
    setAuthMode('login');
    navigate('/auth?mode=login');
  };

  const switchToRegisterMode = () => {
    clearFormFields();
    setAuthMode('register');
    navigate('/auth?mode=register');
  };

  const handleLoginSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage('');
    setIsSubmitting(true);
    try {
      await authAPI.login(username, password);
      setSuccessMessage('Signed in! Redirecting...');
      setTimeout(() => { onLoginSuccess(); navigate('/dashboard'); }, 800);
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || 'Invalid username or password.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegisterSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage('');
    setIsSubmitting(true);
    try {
      await authAPI.register({
        name: fullName, username, email, password,
        mobile_number: parseInt(mobileNumber, 10) || 0,
      });
      setSuccessMessage('Account created! Signing you in...');
      clearFormFields();
      setTimeout(() => switchToLoginMode(), 1500);
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || 'Registration failed. Please check your details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const loginWithGoogle = async () => {
    setErrorMessage('');
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const idToken = await result.user.getIdToken();
      await authAPI.googleLogin(idToken);
      onLoginSuccess();
      navigate('/dashboard');
    } catch (error) {
      // Firebase auth errors always have codes starting with 'auth/'
      if (error.code && String(error.code).startsWith('auth/')) {
        const firebaseErrors = {
          'auth/popup-closed-by-user': 'Sign-in popup was closed. Please try again.',
          'auth/popup-blocked': 'Popup blocked — please allow popups for this site and try again.',
          'auth/unauthorized-domain': 'This domain is not authorised in Firebase. Ask the admin to add it in Firebase Console → Authentication → Settings → Authorised Domains.',
          'auth/cancelled-popup-request': 'Another sign-in is already in progress.',
          'auth/network-request-failed': 'Firebase network error. Check your internet connection.',
          'auth/internal-error': 'Firebase internal error. Please try again.',
        };
        setErrorMessage(firebaseErrors[error.code] || `Firebase sign-in error: ${error.code}`);
      } else if (error.code === 'ERR_NETWORK' || error.code === 'ERR_BAD_RESPONSE' || error.message === 'Network Error') {
        // Axios network error — backend is unreachable
        setErrorMessage(
          'Cannot reach the backend server. Make sure the API URL is correctly set and the server is running.'
        );
      } else {
        // Backend returned an error response
        setErrorMessage(error.response?.data?.detail || `Google sign-in failed. Please try again.`);
      }
      console.error('[Google Login Error]', error);
    }
  };

  return (
    <div className="auth-page">

      {/* ── Left: Brand Panel ─────────────────────────────────── */}
      <div className="auth-brand-panel" aria-hidden="true">
        {/* Logo */}
        <div className="auth-brand-logo">
          <span className="auth-brand-logo-mark">✦</span>
          <span className="auth-brand-logo-text">Lovable</span>
        </div>

        {/* Central editorial copy */}
        <div className="auth-brand-body">
          <h2 className="auth-brand-headline">
            Build any website
            <br />
            <span className="auth-brand-headline-dim">with one prompt.</span>
          </h2>
          <div className="auth-brand-steps">
            <div className="auth-brand-step">
              <span className="auth-brand-step-num">01</span>
              <span className="auth-brand-step-text">Describe your website in plain English</span>
            </div>
            <div className="auth-brand-step">
              <span className="auth-brand-step-num">02</span>
              <span className="auth-brand-step-text">Watch Lovable generate real code instantly</span>
            </div>
            <div className="auth-brand-step">
              <span className="auth-brand-step-num">03</span>
              <span className="auth-brand-step-text">Refine with follow-up prompts — no limits</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="auth-brand-footer">
          <p className="auth-brand-footer-text">Lovable / AI Website System / 2026</p>
        </div>
      </div>

      {/* ── Right: Form Panel ─────────────────────────────────── */}
      <div className="auth-form-panel">
        {/* Back button */}
        <button
          id="auth-back-to-home-button"
          className="auth-back-button"
          onClick={() => navigate('/')}
          aria-label="Back to Home"
        >
          ← Back to Home
        </button>

        <div className="auth-card" role="main">
          {/* Logo (visible on mobile when brand panel is hidden) */}
          <div className="auth-card-logo">
            <span className="auth-card-logo-mark">✦</span>
            <span className="auth-card-logo-text">Lovable</span>
          </div>

          {/* Title */}
          <h1 className="auth-card-title">
            {authMode === 'login' ? 'Welcome back.' : 'Create account.'}
          </h1>
          <p className="auth-card-subtitle">
            {authMode === 'login'
              ? 'Sign in to continue building'
              : 'Start building for free — no credit card needed'}
          </p>

          {/* Feedback */}
          {errorMessage && (
            <div className="auth-error-message" role="alert">{errorMessage}</div>
          )}
          {successMessage && (
            <div className="auth-success-message" role="status">{successMessage}</div>
          )}

          {/* ── Login Form ──────────────────────────────────────── */}
          {authMode === 'login' ? (
            <form id="login-form" onSubmit={handleLoginSubmit}>
              <div className="auth-form-field">
                <label htmlFor="login-username">Username</label>
                <input
                  id="login-username"
                  type="text"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoComplete="username"
                />
              </div>
              <div className="auth-form-field">
                <label htmlFor="login-password">Password</label>
                <input
                  id="login-password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
              </div>

              <div className="auth-submit-wrapper">
                <button
                  id="login-submit-button"
                  type="submit"
                  className="auth-primary-btn"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Signing in...' : 'Sign In'}
                </button>
              </div>

              <p className="auth-switch-text">
                Don't have an account?{' '}
                <span
                  id="switch-to-register-link"
                  className="auth-switch-link"
                  onClick={switchToRegisterMode}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && switchToRegisterMode()}
                >
                  Create one
                </span>
              </p>
            </form>
          ) : (
            /* ── Register Form ────────────────────────────────── */
            <form id="register-form" onSubmit={handleRegisterSubmit}>
              <div className="auth-form-field">
                <label htmlFor="register-full-name">Full Name</label>
                <input
                  id="register-full-name"
                  type="text"
                  placeholder="Your full name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  autoComplete="name"
                />
              </div>
              <div className="auth-form-field">
                <label htmlFor="register-username">Username</label>
                <input
                  id="register-username"
                  type="text"
                  placeholder="Choose a username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoComplete="username"
                />
              </div>
              <div className="auth-form-field">
                <label htmlFor="register-email">Email Address</label>
                <input
                  id="register-email"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                />
              </div>
              <div className="auth-form-field">
                <label htmlFor="register-mobile-number">Mobile Number</label>
                <input
                  id="register-mobile-number"
                  type="tel"
                  placeholder="Your mobile number"
                  value={mobileNumber}
                  onChange={(e) => setMobileNumber(e.target.value)}
                  required
                  autoComplete="tel"
                />
              </div>
              <div className="auth-form-field">
                <label htmlFor="register-password">Password</label>
                <input
                  id="register-password"
                  type="password"
                  placeholder="Choose a strong password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                />
              </div>

              <div className="auth-submit-wrapper">
                <button
                  id="register-submit-button"
                  type="submit"
                  className="auth-primary-btn"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Creating account...' : 'Create Account'}
                </button>
              </div>

              <p className="auth-switch-text">
                Already have an account?{' '}
                <span
                  id="switch-to-login-link"
                  className="auth-switch-link"
                  onClick={switchToLoginMode}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && switchToLoginMode()}
                >
                  Sign In
                </span>
              </p>
            </form>
          )}

          {/* Divider */}
          <div className="auth-divider">
            <div className="auth-divider-line" />
            <span className="auth-divider-text">or</span>
            <div className="auth-divider-line" />
          </div>

          {/* Google */}
          <div className="auth-google-wrapper">
            <button
              className="auth-google-btn"
              onClick={loginWithGoogle}
              disabled={isSubmitting}
              type="button"
            >
              {/* Google G SVG */}
              <svg className="auth-google-icon" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
                <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuthPage;
