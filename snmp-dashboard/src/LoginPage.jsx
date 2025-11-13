// src/LoginPage.jsx

import React, { useState } from 'react';
import { useUser } from './UserContext.jsx';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css'; // We'll create this

function LoginPage() {
  // State for the form fields
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const [isLoading, setIsLoading] = useState(false);

  const { login } = useUser(); // Get the login function from context
  const navigate = useNavigate(); // Get the navigate function to redirect

  const handleSubmit = async (e) => { // <-- 1. Add 'async'
    e.preventDefault();
    setError(null);
    setIsLoading(true); // <-- Let's add this for better UX

    try {
      // 2. Add 'await'
      const success = await login(username, password); 

      if (success) {
        navigate('/'); // Now this only happens *after* login
      }
    } catch (err) {
      // 3. Catch errors from the API (like wrong password)
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false); // Stop loading no matter what
    }
  };

  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h2>SNMP Monitor Login</h2>
        
        {/* Show error if one exists */}
        {error && <p className="error-message">{error}</p>}
        
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        
        <button type="submit" className="login-button">Login</button>
      </form>
    </div>
  );
}

export default LoginPage;