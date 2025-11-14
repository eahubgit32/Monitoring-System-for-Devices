// src/LoginPage.jsx

import React, { useState } from 'react';
import { useUser } from './UserContext.jsx';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css'; // <-- This file will have the new styles

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useUser();
  const navigate = useNavigate();

  // This state controls the theme.
  // We keep it 'true' to force the dark theme.
  const [isDarkMode, setIsDarkMode] = useState(true);
  const themeClass = isDarkMode ? 'dark-mode' : '';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const success = await login(username, password); 
      if (success) {
        navigate('/');
      }
    } catch (err) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // This is now the main full-screen container
    <div className={`login-container ${themeClass}`}>
      
      {/* --- 1. NEW: THE BRANDING PANEL (LEFT SIDE) --- */}
      <div className={`login-branding-panel ${themeClass}`}>
        <h1>SNMP MONITORING</h1>
        <p>Network device performance and health monitoring.</p>
        {/* You could add a logo <img /> tag here later */}
      </div>

      {/* --- 2. NEW: THE FORM WRAPPER (RIGHT SIDE) --- */}
      <div className={`login-form-wrapper ${themeClass}`}>
        
        {/* --- 3. YOUR EXISTING FORM GOES INSIDE --- */}
        <form className={`login-form ${themeClass}`} onSubmit={handleSubmit}>
          {/* A simpler title for this context */}
          <h2>Welcome!</h2>
          
          {error && <p className={`error-message ${themeClass}`}>{error}</p>}
          
          <div className={`form-group ${themeClass}`}>
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
            />
          </div>
          
          <div className={`form-group ${themeClass}`}>
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
            />
          </div>
          
          <button 
            type="submit" 
            className={`login-button ${themeClass}`}
            disabled={isLoading}
          >
            {isLoading ? 'Logging In...' : 'Login'}
          </button>
        </form>
      </div>

    </div>
  );
}

export default LoginPage;