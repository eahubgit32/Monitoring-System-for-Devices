import React, { useState, useEffect, useMemo } from 'react';
import './DiscoverDevice.css';
import { getCookie } from './api/deviceService';


/*  SNMP Device Discovery App
    This React application provides a user interface for discovering SNMP-enabled devices on a network.
    Users can input the target device's IP address and SNMPv3 credentials, triggering a backend API call
    to perform the discovery. The app displays confirmation messages and detailed device information
    upon successful discovery.

    Note: To import this component, ensure:
    - App.css is located in the same directory as App.jsx
    - The backend API endpoint '/api/discover/' is correctly set up to handle POST requests with the expected JSON payload.
      - In urls.py of the app, include the path: path('discover/', views.device_discovery_api, name='device_discovery_api'),
      - In urls.py of the project, include the app's urls: path('api/', include('monitoring.urls')),
*/


// Main DiscoverDevice component
const DiscoverDevice = () => {
  const DJANGO_API_BASE_URL = 'http://localhost:8000/api';

  /*  State Definitions
      - formData: Holds the values of the four input fields.
      - deviceDetails: Holds the response data from the backend after a successful discovery.
      - confirmationMessage: Holds messages to inform the user about the status of their actions.
  */
  const [formData, setFormData] = useState({
    ipAddress: '',
    username: '',
    authPassword: '',
    privPassword: '',
  });
  const [deviceDetails, setDeviceDetails] = useState(null);
  const [confirmationMessage, setConfirmationMessage] = useState('');

  // Brand, Type, Model selection states
  const [brands, setBrands] = useState([]);
  const [types, setTypes] = useState([]);
  const [allModels, setAllModels] = useState([]);

  // User selections
  const [selectedBrandId, setSelectedBrandId] = useState('');
  const [selectedTypeId, setSelectedTypeId] = useState('');
  const [selectedModelId, setSelectedModelId] = useState('');

  // Fetch metadata from Django API on component mount
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        // Fetch all metadata from the new endpoint
        const response = await fetch(`${DJANGO_API_BASE_URL}/metadata/`);
        if (!response.ok) {
          throw new Error(`Failed to fetch metadata: ${response.statusText}`);
        }
        const data = await response.json();
        
        // Populate state from API (using field names from serializer)
        setBrands(data.brands.map(b => ({ id: b.id, name: b.brand_name })));
        setTypes(data.types.map(t => ({ id: t.id, name: t.type_name })));
        setAllModels(data.models);
        
      } catch (error)
      {
        console.error("Metadata fetch error:", error);
        setConfirmationMessage(`❗ Error: Could not load device metadata from server.`);
      }
    };
    
    fetchMetadata();
  }, []); // Empty dependency array ensures this runs once on mount

  /*  Event Handlers 
      - handleInputChange: Updates formData state when input fields change.
      - handleModelSelectChange: Updates model selection states when dropdowns change.
      - handleSubmit: Handles form submission, sends data to backend, and processes the response.
      - resetDeviceDetails: Resets the device details and form for a new search.
  */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  const handleModelSelectChange = (e) => {
    const { name, value } = e.target;
    if (name === 'brand') {
        setSelectedBrandId(value);
        setSelectedTypeId(''); 
        setSelectedModelId(''); 
    } else if (name === 'type') {
        setSelectedTypeId(value);
        setSelectedModelId(''); 
    } else if (name === 'model') {
        setSelectedModelId(value);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setDeviceDetails(null);
    setSelectedBrandId('');
    setSelectedTypeId('');
    setSelectedModelId('');
    
    // Simple validation to ensure all fields are filled
    const missingFields = Object.keys(formData).filter(key => formData[key].trim() === '');
    if (missingFields.length > 0) {
      setConfirmationMessage('❗Please fill in all required fields.');
      return;
    }    

    // Set a confirmation message and clear the sensitive password fields
    const { ipAddress } = formData;
    console.log(`Device Search Initiated for IP: ${ipAddress}.`);
    setConfirmationMessage(`🔍 Device Search Initiated for IP: ${ipAddress}.`);
    // console.log('Search Data:', formData);
    setFormData(prevData => ({
      ipAddress: prevData.ipAddress,
      username: prevData.username,
      authPassword: '', 
      privPassword: '',
    }));

    // Send POST request to the backend API
    console.log("Sending discovery request to backend...");
    const response = await fetch(`${DJANGO_API_BASE_URL}/discover/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData), 
        credentials: 'include',
      });
    const result = await response.json();
    console.log("Response received");
    if (!response.ok || result.status === 'error') {
      // Failure path
      setConfirmationMessage(`❗ Discovery Failed: ${result.message || "Unknown error."}`);
      setDeviceDetails(null); // Clear previous results on failure
    } else {
      // Success path
      setConfirmationMessage(`✅ Discovery Successful for IP: ${ipAddress}.`);
      setDeviceDetails(result.data); // Assuming the device details are in result.data
    }
  };

  const resetDeviceDetails = () => {
    setDeviceDetails(null);
    setConfirmationMessage('');
    setSelectedBrandId('');
    setSelectedTypeId('');
    setSelectedModelId('');
    setFormData({
      ipAddress: '',
      username: '',
      authPassword: '',
      privPassword: '',
    });
  }

  const handleConfirmAddDevice = async () => {
    if (!deviceDetails) {
      setConfirmationMessage("❗ Please discover a device first.");
      return;
    }
    
    if (!selectedModelId) {
      setConfirmationMessage("❗ Please select the correct device model from the dropdowns before adding.");
      return;
    }

    console.log("Confirming Add Device: ", deviceDetails.hostname);
    const payload = {
      ip_address: deviceDetails.ip_address,
      hostname: deviceDetails.hostname,
      model_id: parseInt(selectedModelId, 10),
      // snmpv3_credentials: deviceDetails.snmpv3_credentials,
      raw_discovery_data: {
        data: deviceDetails
      }
    };

    setConfirmationMessage(`Registering device ${deviceDetails.hostname}...`);

    try {
      // --- ACTUAL REGISTRATION API CALL ---
      console.log("Registration Payload:", payload);
      const csrfToken = getCookie('csrftoken');
      console.log("Using CSRF Token:", csrfToken);
      const response = await fetch(`${DJANGO_API_BASE_URL}/device/register/`, { 
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          // Add CSRF token if not using @csrf_exempt
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(payload),
        credentials: 'include',
      });

      const result = await response.json();

      if (response.ok) { // Check if status code is 2xx
        setConfirmationMessage(`✅ Device ${result.hostname} registered successfully! Closing in 5 seconds...`);
        setTimeout(() => resetDeviceDetails(), 5000); 
      } else {
        // Use 'detail' from DRF or 'message' from your custom error
        setConfirmationMessage(`❗ Registration Failed: ${result.detail || result.message || "Unknown server error."}`);
      }
    } catch (error) {
      console.error('Registration Fetch Error:', error);
      setConfirmationMessage('❗ Network Error: Could not reach the registration endpoint.');
    }
  };

  // Form input fields configuration
  const inputFields = [
    { id: 'ipAddress', name: 'ipAddress', label: 'IP Address', type: 'text', placeholder: 'e.g., 192.168.32.2' },
    { id: 'username', name: 'username', label: 'User Name', type: 'text', placeholder: 'e.g., switchB' },
    { id: 'authPassword', name: 'authPassword', label: 'Auth Password', type: 'password', placeholder: 'SHA/MD5 Password' },
    { id: 'privPassword', name: 'privPassword', label: 'Priv Password', type: 'password', placeholder: 'AES/DES Password' },
  ];
  
  // Other variable definitions
  const isSuccess = confirmationMessage.startsWith('✅');
  const isError = confirmationMessage.startsWith('❗');
  const confirmationClass = isSuccess ? 'success' : isError ? 'error' : 'loading';

  // Other function definitions
  // Filter models based on selected brand and type
  const filteredModels = useMemo(() => {
    let filtered = allModels;
    
    const brandIdInt = parseInt(selectedBrandId, 10);
    const typeIdInt = parseInt(selectedTypeId, 10);
    
    // Filter by Brand ID
    if (brandIdInt) {
        filtered = filtered.filter(m => m.brandId === brandIdInt);
    }
    
    // Filter by Type ID
    if (typeIdInt) {
        filtered = filtered.filter(m => m.typeId === typeIdInt);
    }
    
    // Auto-selection/cleanup logic
    if (filtered.length === 1 && filtered[0].id) {
         if (filtered[0].id.toString() !== selectedModelId) {
            setSelectedModelId(filtered[0].id.toString());
         }
    } else if (filtered.length > 1 && selectedModelId && !filtered.find(m => m.id.toString() === selectedModelId)) {
        setSelectedModelId('');
    } else if (filtered.length === 0) {
        setSelectedModelId('');
    }

    return filtered;
  }, [allModels, selectedBrandId, selectedTypeId, selectedModelId]);

    const getCsrfToken = () => {
        return getCookie('csrftoken');
    }







  // --- Input Form Structure ---
  const renderInputFields = () => {
    return (
      <div className="form-card">
        <h1 className="form-title">
          SNMP Device Discovery
        </h1>
        <p className="form-subtitle">
          Enter the target device's IP and SNMPv3 credentials to begin the discovery process.
        </p>

        {/* Confirmation/Error Message Box */}
        {confirmationMessage && (
          <div 
            role="alert" 
            className={`confirmation-box ${confirmationClass}`}
          >
            <span>{confirmationMessage}</span>
          </div>
        )}

        {/* The main form element */}
        <form onSubmit={handleSubmit} className="form-fields">
          {inputFields.map(field => (
            <div key={field.id} className="input-group">
              <label htmlFor={field.id} className="label">
                {field.label}
              </label>
              <input
                id={field.id}
                name={field.name}
                type={field.type}
                value={formData[field.name]}
                onChange={handleInputChange}
                placeholder={field.placeholder}
                className="input-field"
                aria-label={field.label}
                required
              />
            </div>
          ))}

          <button
            type="submit"
            className="submit-button"
          >
            <span className="button-icon">🔍</span>
            Search device
          </button>
        </form>
      </div>
    );
  }

  // --- Device Details Display ---
  const renderDeviceDetails = () => {
    const { 
      hostname, 
      ip_address, 
      model_id_raw, 
      applicable_measurements, 
      interfaces 
    } = deviceDetails;

    // Helper to format OID/Measurement values
    const formatValue = (key) => {
      const measurement = applicable_measurements[key];
      // Handle case where SNMP value retrieval failed for a specific OID
      if (measurement.note && measurement.note.includes("error")) return <span className="value-error-note">N/A (Error)</span>;
      if (measurement.value === "SNMP Error: No OID Found") return <span className="value-na-note">N/A</span>;
      
      // Simple formatting helper (bytes for memory, percent for CPU)
      if (key.includes('memory')) {
        const bytes = parseInt(measurement.value, 10);
        if (isNaN(bytes)) return <span className="value-na-note">N/A ({measurement.value})</span>;
        // Convert bytes to MB for display
        return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
      }
      if (key.includes('cpu')) {
        return `${measurement.value} %`;
      }
      return measurement.value; // Default return for other types
    };
    
    // Helper to format Measurement Key name (e.g., cpu_usage -> CPU Usage)
    const formatKeyName = (key) => key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    // Get current selected model display name
    const currentModelDisplay = allModels.find(m => m.id.toString() === selectedModelId)?.display || '';

    // Return of Device Details
    return (
      <div className="details-main-container">
        {confirmationMessage && (
          <div 
            role="alert" 
            className={`confirmation-box ${confirmationClass}`}
          >
            <span>{confirmationMessage}</span>
          </div>
        )}
        <div className="details-header-wrapper">
          <h1 className="details-title">
            Discovery Results: {hostname}
          </h1>
          <div className="details-actions">
            <button 
              onClick={() => resetDeviceDetails(null)} 
              className="new-search-button"
              onMouseOver={e => e.currentTarget.style.backgroundColor = '#e5e7eb'}
              onMouseOut={e => e.currentTarget.style.backgroundColor = '#f3f4f6'}
            >
              <span className="button-icon-large">←</span> New Search
            </button>
            <button 
              className="confirm-add-button"
              onClick={handleConfirmAddDevice}
              disabled={!selectedModelId}
            >
              <span className="button-icon-large">➕</span> Confirm Add Device
            </button>
          </div>
        </div>

        {/* Model Selection Card */}
        <div className="model-selection-card">
            <h2 className="info-card-title">1. Confirm Device Model (Required)</h2>
            
            <div className="info-grid" style={{marginBottom: '1rem', gridTemplateColumns: '1fr'}}>
                <p><strong>IP Address:</strong> {ip_address}</p>
                <p className="info-long-text"><strong>Raw Model ID (OID):</strong> {model_id_raw}</p>
            </div>
            
            <div className="model-selection-grid">
                {/* Brand Selection */}
                <div className="model-select-group">
                    <label htmlFor="brand-select" className="model-select-label">Brand</label>
                    <select 
                        id="brand-select"
                        name="brand"
                        value={selectedBrandId}
                        onChange={handleModelSelectChange}
                        className="model-select-field"
                    >
                        <option value="">-- Select Brand --</option>
                        {brands.map(brand => (
                            <option key={brand.id} value={brand.id.toString()}>{brand.name}</option>
                        ))}
                    </select>
                </div>
                
                {/* Type Selection */}
                <div className="model-select-group">
                    <label htmlFor="type-select" className="model-select-label">Type</label>
                    <select 
                        id="type-select"
                        name="type"
                        value={selectedTypeId}
                        onChange={handleModelSelectChange}
                        className="model-select-field"
                        disabled={!selectedBrandId && brands.length > 0} 
                    >
                        <option value="">-- Select Type --</option>
                        {types.map(type => (
                            <option key={type.id} value={type.id.toString()}>{type.name}</option>
                        ))}
                    </select>
                </div>
                
                {/* Model Selection */}
                <div className="model-select-group">
                    <label htmlFor="model-select" className="model-select-label">Model</label>
                    <select 
                        id="model-select"
                        name="model"
                        value={selectedModelId}
                        onChange={handleModelSelectChange}
                        className="model-select-field"
                        disabled={!selectedBrandId || filteredModels.length === 0} 
                    >
                        <option value="">
                            {filteredModels.length === 0 ? 'No models available' : '-- Select Model --'}
                        </option>
                        {filteredModels.map(model => (
                            <option key={model.id} value={model.id.toString()}>{model.display}</option>
                        ))}
                    </select>
                    {currentModelDisplay && (
                        <p style={{fontSize: '0.75rem', color: '#10b981', marginTop: '0.25rem', fontWeight: 600}}>
                            Selected: {currentModelDisplay}
                        </p>
                    )}
                    {filteredModels.length === 0 && (selectedBrandId || selectedTypeId) && (
                        <p style={{fontSize: '0.75rem', color: '#dc2626', marginTop: '0.25rem'}}>
                            No models match the current selection.
                        </p>
                    )}
                </div>
            </div>
        </div>
        
        {/* General Info Card */}
        {/*}
        <div className="info-card-container">
          <h2 className="info-card-title">Overview</h2>
          <div className="info-grid">
            <p><strong>IP Address:</strong> {ip_address}</p>
            <p className="info-long-text"><strong>Raw Model ID (OID):</strong> {model_id_raw}</p>
          </div>
        </div>
        */}

        {/* Measurements/Metrics Section */}
        <div className="metrics-card-container">
          <h2 className="metrics-card-title">2. Applicable Metrics</h2>
          <div className="metrics-grid">
            {Object.keys(applicable_measurements).map(key => (
              <div key={key} className="metric-item">
                <p className="metric-label">
                  {formatKeyName(key)}
                </p>
                <p className="metric-value">
                  {formatValue(key)}
                  {key.includes('cpu') && <span className="metric-note-small">(Last 5 Mins)</span>}
                  {key.includes('memory') && <span className="metric-note-small">(Estimated)</span>}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Interfaces Section */}
        <div className="interfaces-card-container">
          <h2 className="interfaces-card-title">
            3. Enabled Interfaces ({interfaces ? interfaces.names.length : 0})
            Active ({interfaces ? interfaces.oper_status.filter(status => status.startsWith('up')).length : 0})
          </h2>
          {interfaces && interfaces.names.length > 0 ? (
            <div className="interface-list-wrapper">
              {interfaces.names.map((name, index) => (interfaces.admin_status[index].startsWith('up') ? (
                <span key={index}
                className={`interface-tag-base ${interfaces.oper_status[index].startsWith('up') ? 'interface-tag-up' : 'interface-tag-down'}`}
                >
                  {name}
                </span>
              ) : (null)))}
            </div>
          ) : (
            <p className="info-placeholder-text">No enabled interfaces.</p>
          )}
        </div>
      </div>
    );
  };





  // Main conditional renders
  return (
    <div className="app-container">
      {deviceDetails ? renderDeviceDetails() : renderInputFields()}
    </div>
  );
};

export default DiscoverDevice;