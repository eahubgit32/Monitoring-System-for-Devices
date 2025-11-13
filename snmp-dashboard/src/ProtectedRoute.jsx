// src/ProtectedRoute.jsx

import React from 'react';
import { useUser } from './UserContext.jsx';
import { Navigate, Outlet } from 'react-router-dom';

function ProtectedRoute() {
  const { isLoggedIn } = useUser();

  if (!isLoggedIn) {
    // User is not logged in, redirect them to the login page
    return <Navigate to="/login" replace />;
  }

  // User is logged in, show the page they were trying to access
  return <Outlet />;
}

export default ProtectedRoute;