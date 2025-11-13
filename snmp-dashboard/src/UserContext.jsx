// src/UserContext.jsx

import React, { createContext, useState, useContext, useEffect } from 'react';

// This is the new "phone book" for our auth API
const authService = {
  apiBase: 'http://localhost:8000/api',

  // This function handles all API responses
  handleResponse: async (response) => {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP Error! Status: ${response.status}`);
    }
    // For 200 OK, return the JSON data
    // For 204 No Content (like logout), return null
    return response.status !== 204 ? response.json() : null; 
  },

  // This is our NEW login function
  login: async (username, password) => {
    const response = await fetch(`${authService.apiBase}/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
      credentials: 'include' 
    });
    
    // THIS IS THE FIX:
    // We call handleResponse, but also get the data
    const data = await authService.handleResponse(response);
    return data; // Return the user data directly
  },

  // This is our NEW logout function
  logout: async () => {
    const response = await fetch(`${authService.apiBase}/logout/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include' // <-- ADD THIS
    });
    return authService.handleResponse(response);
  }
// ...
};

// 1. Create the context
const UserContext = createContext();

// 2. Create the provider
export function UserProvider({ children }) {
  
  // Initialize 'user' state from sessionStorage
  const [user, setUser] = useState(() => {
    try {
      const storedUser = sessionStorage.getItem('snmp-user');
      return storedUser ? JSON.parse(storedUser) : null;
    } catch (error) {
      return null;
    }
  });

  // Sync 'user' state to sessionStorage
  useEffect(() => {
    if (user) {
      sessionStorage.setItem('snmp-user', JSON.stringify(user));
    } else {
      sessionStorage.removeItem('snmp-user');
    }
  }, [user]);

  // --- THIS IS THE UPDATED LOGIN FUNCTION ---
// --- THIS IS THE FIXED LOGIN FUNCTION ---
  const login = async (username, password) => { // <-- 1. Make it async
    try {
      // 2. Await the real API call
      const userData = await authService.login(username, password);
      
      // The data we get back is the REAL user object
      setUser(userData);
      
      return true; // Return true so the LoginPage navigates
    } catch (error) {
      // If authService.login fails (wrong password), it throws an error
      console.error("Login failed:", error);
      throw error; // Re-throw the error so LoginPage can catch it
    }
  };

  // --- THIS IS THE UPDATED LOGOUT FUNCTION ---
  const logout = async () => {
    await authService.logout();
    setUser(null); // Clear the user from state
  };

  const value = {
    user: user,
    isLoggedIn: user !== null,
    login: login,
    logout: logout,
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

// 3. The custom hook to read the context
export function useUser() {
  return useContext(UserContext);
}