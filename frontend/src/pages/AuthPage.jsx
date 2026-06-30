import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authAPI } from '../api';
import './AuthPage.css';

/**
 * AuthPage — handles both Login and Registration in one component.
 * The mode ('login' or 'register') is controlled by the URL query parameter: ?mode=login or ?mode=register.
 */
function AuthPage({ onLoginSuccess }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Read the mode from the URL query string (defaults to 'login')
  const [authMode, setAuthMode] = useState(
    searchParams.get('mode') === 'register' ? 'register' : 'login'
  );

  // Form field states
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [password, setPassword] = useState('');

  // Feedback states
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Update mode when URL param changes
  useEffect(() => {
    const modeFromUrl = searchParams.get('mode');
    if (modeFromUrl === 'register') {
      setAuthMode('register');
    } else {
      setAuthMode('login');
    }
  }, [searchParams]);

  const clearFormFields = () => {
    setFullName('');
    setUsername('');
    setEmail('');
    setMobileNumber('');
    setPassword('');
    setErrorMessage('');
    setSuccessMessage('');
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
      setSuccessMessage('Login successful! Redirecting...');
      setTimeout(() => {
        onLoginSuccess();
        navigate('/dashboard');
      }, 800);
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
        name: fullName,
        username,
        email,
        password,
        mobile_number: parseInt(mobileNumber, 10) || 0,
      });
      setSuccessMessage('Account created! Please sign in.');
      clearFormFields();
      setTimeout(() => switchToLoginMode(), 1500);
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || 'Registration failed. Please check your details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      {/* Background glow */}
      <div className="auth-page-background-glow" />

      {/* Back to landing page link */}
      <button
        id="auth-back-to-home-button"
        className="auth-back-button"
        onClick={() => navigate('/')}
      >
        ← Back to Home
      </button>

      <div className="auth-card">
        {/* Logo */}
        <div className="auth-card-logo">
          <span>💖</span>
          <span className="auth-card-logo-text">Lovable</span>
        </div>

        <h1 className="auth-card-title">
          {authMode === 'login' ? 'Welcome back' : 'Create your account'}
        </h1>
        <p className="auth-card-subtitle">
          {authMode === 'login'
            ? 'Sign in to continue building'
            : 'Start building websites with AI for free'}
        </p>

        {/* Feedback messages */}
        {errorMessage && (
          <div className="auth-error-message">{errorMessage}</div>
        )}
        {successMessage && (
          <div className="auth-success-message">{successMessage}</div>
        )}

        {/* ─── Login Form ─────────────────────────────────────────── */}
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
              />
            </div>
            <button
              id="login-submit-button"
              type="submit"
              className="auth-submit-button"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Signing in...' : 'Sign In'}
            </button>
            <p className="auth-switch-text">
              Don't have an account?{' '}
              <span
                id="switch-to-register-link"
                className="auth-switch-link"
                onClick={switchToRegisterMode}
              >
                Create one
              </span>
            </p>
          </form>
        ) : (
          /* ─── Register Form ────────────────────────────────────── */
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
              />
            </div>
            <button
              id="register-submit-button"
              type="submit"
              className="auth-submit-button"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating account...' : 'Create Account'}
            </button>
            <p className="auth-switch-text">
              Already have an account?{' '}
              <span
                id="switch-to-login-link"
                className="auth-switch-link"
                onClick={switchToLoginMode}
              >
                Sign In
              </span>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}

export default AuthPage;
