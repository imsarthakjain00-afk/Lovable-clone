import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import Templates from './pages/Templates';
import Pricing from './pages/Pricing';

/**
 * App — the root component that sets up all routes and manages login state.
 *
 * Routes:
 *   /              → Landing Page
 *   /auth          → Login / Register
 *   /dashboard     → Main workspace (requires login)
 *   /templates     → Template picker
 *   /pricing       → Pricing page
 */
function App() {
  // isUserLoggedIn is true when a valid JWT token exists in localStorage
  const [isUserLoggedIn, setIsUserLoggedIn] = useState(
    Boolean(localStorage.getItem('auth_token'))
  );

  const handleLoginSuccess = () => {
    setIsUserLoggedIn(true);
  };

  const handleLogout = () => {
    setIsUserLoggedIn(false);
  };

  return (
    <Routes>
      {/* ── Public routes (accessible to everyone) ── */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/templates" element={<Templates />} />

      {/* ── Auth route ── */}
      <Route
        path="/auth"
        element={
          isUserLoggedIn
            ? <Navigate to="/dashboard" replace />
            : <AuthPage onLoginSuccess={handleLoginSuccess} />
        }
      />

      {/* ── Protected route — redirect to /auth if not logged in ── */}
      <Route
        path="/dashboard"
        element={
          isUserLoggedIn
            ? <Dashboard onLogout={handleLogout} />
            : <Navigate to="/auth?mode=login" replace />
        }
      />
      
      <Route
        path="/dashboard/project/:projectId"
        element={
          isUserLoggedIn
            ? <Dashboard onLogout={handleLogout} />
            : <Navigate to="/auth?mode=login" replace />
        }
      />

      {/* ── Catch-all: redirect unknown URLs to the landing page ── */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
