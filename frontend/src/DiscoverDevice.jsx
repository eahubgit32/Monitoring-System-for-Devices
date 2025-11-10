import React, { useState } from 'react';
import './DiscoverDevice.css';


/*  SNMP Device Discovery App
    This React application provides a user interface for discovering SNMP-enabled devices on a network.
    Users can input the target device's IP address and SNMPv3 credentials, triggering a backend API call
    to perform the discovery. The app displays confirmation messages and detailed device information
    upon successful discovery.

    Note: To import this component, ensure:
    - App.css is located in the same directory as App.jsx
    - The backend API endpoint '/api/v1/discover/' is correctly set up to handle POST requests with the expected JSON payload.
      - In urls.py of the app, include the path: path('discover/', views.device_discovery_api, name='device_discovery_api'),
      - In urls.py of the project, include the app's urls: path('api/v1/', include('monitoring.urls')),
*/


// Main DiscoverDevice component
const DiscoverDevice = () => {
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

  /*  Event Handlers 
      - handleInputChange: Updates formData state when input fields change.
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Simple validation to ensure all fields are filled
    const missingFields = Object.keys(formData).filter(key => formData[key].trim() === '');
    if (missingFields.length > 0) {
      setConfirmationMessage('Please fill in all required fields.');
      return;
    }    

    // Set a confirmation message and clear the sensitive password fields
    const { ipAddress } = formData;
    setConfirmationMessage(`✅ Device Search Initiated for IP: ${ipAddress}.`);
    console.log('Search Data:', formData);
    setFormData(prevData => ({
      ipAddress: prevData.ipAddress,
      username: prevData.username,
      authPassword: '', 
      privPassword: '',
    }));

    // Send POST request to the backend API
    const response = await fetch('/api/v1/discover/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData), 
      });
    const result = await response.json();
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
    setFormData({
      ipAddress: '',
      username: '',
      authPassword: '',
      privPassword: '',
    });
  }

  // Form input fields configuration
  const inputFields = [
    { id: 'ipAddress', name: 'ipAddress', label: 'IP Address', type: 'text', placeholder: 'e.g., 192.168.32.2' },
    { id: 'username', name: 'username', label: 'User Name', type: 'text', placeholder: 'e.g., switchB' },
    { id: 'authPassword', name: 'authPassword', label: 'Auth Password', type: 'password', placeholder: 'SHA/MD5 Password' },
    { id: 'privPassword', name: 'privPassword', label: 'Priv Password', type: 'password', placeholder: 'AES/DES Password' },
  ];
  
  // Other variable definitions
  const isSuccess = confirmationMessage.startsWith('✅');
  const confirmationClass = isSuccess ? 'success' : 'error';
  const icon = isSuccess ? '✔' : '❗';





  // Input Form Structure
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
            <span className="button-icon">{icon}</span>
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

  // Device Details Display
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
        if (measurement.note && measurement.note.includes("error")) return <span style={{fontSize: '0.875rem', color: '#ef4444', fontStyle: 'italic'}}>N/A (Error)</span>;
        if (measurement.value === "SNMP Error: No OID Found") return <span style={{fontSize: '0.875rem', color: '#6b7280', fontStyle: 'italic'}}>N/A</span>;
        
        // Simple formatting helper (bytes for memory, percent for CPU)
        if (key.includes('memory')) {
            const bytes = parseInt(measurement.value, 10);
            if (isNaN(bytes)) return <span style={{fontSize: '0.875rem', color: '#6b7280', fontStyle: 'italic'}}>N/A ({measurement.value})</span>;

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


    // Return of Device Details
    return (
      <div style={{backgroundColor: '#ffffff', padding: '2.5rem', borderRadius: '0.75rem', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)', width: '100%', maxWidth: '960px', margin: 'auto', display: 'flex', flexDirection: 'column', gap: '2rem'}}>
        
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid #e5e7eb', paddingBottom: '1rem', marginBottom: '1rem'}}>
            <h1 style={{fontSize: '1.875rem', fontWeight: '800', color: '#4f46e5', marginBottom: '0.75rem'}}>
                Discovery Results: {hostname}
            </h1>
            <button 
                onClick={() => resetDeviceDetails(null)} 
                style={{padding: '0.5rem 1rem', backgroundColor: '#f3f4f6', color: '#4b5563', borderRadius: '0.5rem', transition: 'background-color 0.15s', boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)', display: 'flex', alignItems: 'center', fontWeight: '500', border: 'none', cursor: 'pointer'}}
                onMouseOver={e => e.currentTarget.style.backgroundColor = '#e5e7eb'}
                onMouseOut={e => e.currentTarget.style.backgroundColor = '#f3f4f6'}
            >
                <span style={{fontSize: '1.25rem', marginRight: '0.5rem'}}>←</span> New Search
            </button>
        </div>
        
        {/* General Info Card */}
        <div style={{backgroundColor: '#eef2ff', padding: '1.5rem', borderRadius: '0.75rem', border: '1px solid #c7d2fe', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'}}>
            <h2 style={{fontSize: '1.25rem', fontWeight: '600', color: '#3730a3', marginBottom: '0.75rem', borderBottom: '1px solid #a5b4fc', paddingBottom: '0.5rem'}}>Overview</h2>
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', color: '#374151'}}>
                <p><strong>IP Address:</strong> {ip_address}</p>
                <p style={{wordBreak: 'break-all'}}><strong>Raw Model ID (OID):</strong> {model_id_raw}</p>
            </div>
        </div>

        {/* Measurements/Metrics Section */}
        <div style={{backgroundColor: '#ffffff', padding: '1.5rem', borderRadius: '0.75rem', border: '1px solid #e5e7eb', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'}}>
            <h2 style={{fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', marginBottom: '1rem', borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem'}}>Applicable Metrics</h2>
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem'}}>
                {Object.keys(applicable_measurements).map(key => (
                    <div key={key} style={{padding: '1rem', backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '0.5rem', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)'}}>
                        <p style={{fontSize: '0.875rem', fontWeight: '500', color: '#6b7280', marginBottom: '0.25rem'}}>
                            {formatKeyName(key)}
                        </p>
                        <p style={{fontSize: '1.125rem', fontWeight: '700', color: '#1f2937'}}>
                            {formatValue(key)}
                            {key.includes('cpu') && <span style={{fontSize: '0.75rem', color: '#6b7280', marginLeft: '0.5rem'}}>(Last 5 Mins)</span>}
                            {key.includes('memory') && <span style={{fontSize: '0.75rem', color: '#6b7280', marginLeft: '0.5rem'}}>(Estimated)</span>}
                        </p>
                    </div>
                ))}
            </div>
        </div>

        {/* Interfaces Section */}
        <div style={{backgroundColor: '#ffffff', padding: '1.5rem', borderRadius: '0.75rem', border: '1px solid #e5e7eb', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'}}>
            <h2 style={{fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', marginBottom: '1rem', borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem'}}>Enabled Interfaces ({interfaces ? interfaces.names.length : 0})</h2>

            {interfaces && interfaces.names.length > 0 ? (
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.5rem', fontSize: '0.875rem', maxHeight: '12rem', overflowY: 'auto', padding: '0.5rem', border: '1px dashed #d1d5db', borderRadius: '0.5rem'}}>
                    {interfaces.names.map((name, index) => (interfaces.oper_status[index].startsWith('up') ? (
                        <span key={index} style={{backgroundColor: '#d1fae5', color: '#065f46', padding: '0.25rem 0.75rem', borderRadius: '9999px', textAlign: 'center', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)', transition: 'background-color 0.1s'}}
                        onMouseOver={e => e.currentTarget.style.backgroundColor = '#a7f3d0'}
                        onMouseOut={e => e.currentTarget.style.backgroundColor = '#d1fae5'}
                        >
                            {name}
                        </span>
                    ) : (null)))}
                </div>
            ) : (
                <p style={{color: '#6b7280', fontStyle: 'italic'}}>No enabled interfaces.</p>
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