// src/main.jsx

import React from 'react';
import ReactDOM from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { UserProvider } from './UserContext.jsx'; 

import './index.css';
import App from './App.jsx'; // Your main layout
import ProtectedRoute from './ProtectedRoute.jsx'; // <-- 1. IMPORT
import DashboardPage from './DashboardPage.jsx';
import DeviceDetailsPage from './DeviceDetailsPage.jsx';
import LoginPage from './LoginPage.jsx';
import AddDevicePage from './AddDevicePage.jsx'; // <-- 1. IMPORT
import EditDevicePage from './EditDevicePage.jsx'; // <-- 1. IMPORT

const router = createBrowserRouter([
  {
    path: "/",
    element: <ProtectedRoute />, // <-- 2. USE THE BOUNCER
    children: [
      {
        path: "/",
        element: <App />, // <-- 3. 'App' is now the layout *inside* protection
        children: [
          // These pages are now all protected
          {
            path: "/",
            element: <DashboardPage />,
          },
          {
            path: "/device/:deviceId",
            element: <DeviceDetailsPage />,
          },
          {
            path: "/add-device",
            element: <AddDevicePage />,
          },
          {
            path: "/edit-device/:deviceId",
            element: <EditDevicePage />,
          }
        ],
      },
    ]
  },
  {
    path: "/login",
    element: <LoginPage />, // The login page is NOT protected
  },
]);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <UserProvider>
      <RouterProvider router={router} />
    </UserProvider>
  </React.StrictMode>
);