// src/App.jsx - Last Known Stable Header Logic

import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useUser } from './UserContext.jsx'; 
import './App.css'; 

function App() {
  const { user, logout } = useUser();
  const navigate = useNavigate();

  const handleLogout = () => {
    // ... (Your existing logout logic)
    logout();
    navigate('/login'); 
  };

  return (
    <div>
      <header className="app-header">
        <div className="header-content">
          {/* CRITICAL FIX: Ensures the correct username is displayed */}
          <span>Welcome, <strong>{user?.username || 'Guest'}</strong></span> 
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </header>
      
      <main>
        <Outlet />
      </main>
    </div>
  );
}

export default App;