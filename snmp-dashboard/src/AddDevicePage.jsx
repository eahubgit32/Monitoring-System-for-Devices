// src/AddDevicePage.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { deviceService } from './api/deviceService.js';
import { useUser } from './UserContext.jsx';
import './LoginPage.css';

function AddDevicePage() {
  const [formData, setFormData] = useState({
    hostname: '',
    ipAddress: '',
    modelId: '',
  });
  
  const [models, setModels] = useState([]); 
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const { user } = useUser();
  const navigate = useNavigate();

  // 2. FETCH MODELS ON PAGE LOAD
  useEffect(() => {
    const fetchModels = async () => {
      setIsLoading(true);
      try {
        const modelsData = await deviceService.getDeviceModels();
        setModels(modelsData);
        // Set a default for the dropdown
        if (modelsData.length > 0) {
          setFormData(prevData => ({ ...prevData, modelId: modelsData[0].id }));
        }
      } catch (e) {
        setError(e.message);
      }
      setIsLoading(false);
    };
    fetchModels();
  }, []); // Empty array [] means run once

  // 3. HANDLE FORM SUBMIT
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      // Pass 'formData' and 'user'. No token needed.
      await deviceService.addDevice(formData, user);
      
      setIsLoading(false);
      navigate('/');
      
    } catch (e) {
      setError(e.message);
      setIsLoading(false);
    }
  };

  // 4. HANDLE FORM INPUT CHANGES (No change needed)
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h2>Add New Device</h2>
        
        {error && <p className="error-message">{error}</p>}
        
        {/* 5. THE NEW FORM (No change needed) */}
        <div className="form-group">
          <label htmlFor="hostname">Hostname</label>
          <input
            type="text"
            name="hostname"
            id="hostname"
            placeholder="e.g., Core-Router-01"
            value={formData.hostname}
            onChange={handleChange}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="ipAddress">Device IP Address</label>
          <input
            type="text"
            name="ipAddress"
            id="ipAddress"
            placeholder="e.g., 192.168.1.1"
            value={formData.ipAddress}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="modelId">Device Model</label>
          <select
            name="modelId"
            id="modelId"
            value={formData.modelId}
            onChange={handleChange}
            disabled={isLoading}
          >
            {models.map(model => (
              <option key={model.id} value={model.id}>
                {model.model_name}
              </option>
            ))}
          </select>
        </div>
        
        <button type="submit" className="login-button" disabled={isLoading}>
          {isLoading ? 'Adding...' : 'Add Device'}
        </button>
        
        <Link to="/" style={{textAlign: 'center', display: 'block', marginTop: '20px'}}>
          Cancel
        </Link>
      </form>
    </div>
  );
}

export default AddDevicePage;