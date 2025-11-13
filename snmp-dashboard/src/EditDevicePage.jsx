// src/EditDevicePage.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { deviceService } from './api/deviceService.js';
import './LoginPage.css'; // Re-using login styles

function EditDevicePage() {
  const [deviceName, setDeviceName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const { deviceId } = useParams(); // Get the ID from the URL
  const navigate = useNavigate();

  // 1. FETCH THE DEVICE'S CURRENT DATA ON LOAD
  useEffect(() => {
    const fetchDevice = async () => {
      setIsLoading(true);
      try {
        const data = await deviceService.getDeviceById(deviceId);
        setDeviceName(data.device.name); // Set the form field
      } catch (e) {
        setError(e.message);
      }
      setIsLoading(false);
    };
    fetchDevice();
  }, [deviceId]);

  // 2. HANDLE THE FORM SUBMIT
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // Call the "update" service function
      await deviceService.updateDevice(deviceId, deviceName);
      setIsLoading(false);
      navigate('/'); // Go back to dashboard on success
      
    } catch (e) {
      setError(e.message);
      setIsLoading(false);
    }
  };
  
  if (isLoading) {
    return <div className="loading-spinner">Loading device data...</div>
  }

  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h2>Edit Device</h2>
        
        {error && <p className="error-message">{error}</p>}
        
        <div className="form-group">
          <label htmlFor="devicename">Device Name</label>
          <input
            type="text"
            id="devicename"
            value={deviceName}
            onChange={(e) => setDeviceName(e.target.value)}
          />
        </div>
        
        <button type="submit" className="login-button" disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Save Changes'}
        </button>
        
        <Link to="/" style={{textAlign: 'center', display: 'block', marginTop: '20px'}}>
          Cancel
        </Link>
      </form>
    </div>
  );
}

export default EditDevicePage;