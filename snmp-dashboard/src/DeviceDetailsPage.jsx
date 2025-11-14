// src/DeviceDetailsPage.jsx - MODIFIED VERSION

import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { deviceService } from './api/deviceService.js';
import './DeviceDetailsPage.css';
// We'll re-use the table styles from the dashboard
import './DeviceTable.css'; 

function DeviceDetailsPage() {
  const { deviceId } = useParams();
  
  // --- STATE (We add 'interfaces' state) ---
  const [device, setDevice] = useState(null);
  const [interfaces, setInterfaces] = useState([]); // <-- NEW STATE
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // --- DATA FETCHING (This is updated) ---
  useEffect(() => {
    const fetchAllData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Fetch both device and interface data at the same time
        const [deviceData, interfaceData] = await Promise.all([
          deviceService.getDeviceById(deviceId),
          deviceService.getDeviceInterfaces(deviceId)
        ]);
        
        setDevice(deviceData.device);
        setInterfaces(interfaceData); // <-- SET NEW STATE

      } catch (e) {
        setError(e.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAllData();
  }, [deviceId]); // Re-fetch if the deviceId in the URL changes

  // --- RENDER LOGIC ---
  if (isLoading) {
    return <div className="loading-spinner">Loading device details...</div>;
  }

  if (error) {
    return <div className="error-message">Error: {error}</div>;
  }
  if (!device) {
    return <div>Device not found.</div>;
  }

  // --- Status Calculations (run only after 'device' is loaded) ---
  const cpu_status = device.measurements.cpu?.status || 'good';
  const mem_status = device.measurements.memory?.status || 'good';

  const usedMemoryMB = (device.measurements.memory?.used_bytes || 0) / (1024 * 1024);
  const freeMemoryMB = (device.measurements.memory?.free_bytes || 0) / (1024 * 1024);
  const totalMemoryMB = usedMemoryMB + freeMemoryMB;

  return (
    <div className="details-container">
      <Link to="/">&larr; Back to Dashboard</Link>
      
      <h1>{device.name}</h1> 
      <span className={`status-badge status-${device.status}`}> 
        {device.status}
      </span>

      {/* --- DEVICE METRICS GRID (Unchanged) --- */}
      <h2>Device Metrics</h2>
      <div className="details-grid">
        <div className="detail-item">
          <strong>IP Address:</strong>
          <span>{device.ip_address}</span>
        </div>
        
        <div className={`detail-item metric-${cpu_status}`}>
          <strong>CPU Usage:</strong>
          <span>{device.measurements.cpu?.value}%</span>
        </div>
        
        <div className={`detail-item metric-${mem_status}`}>
          <strong>Memory Used (MB):</strong>
          <span>{usedMemoryMB.toFixed(0)} MB</span>
        </div>
        
        <div className={`detail-item metric-${mem_status}`}>
          <strong>Memory Free (MB):</strong>
          <span>{freeMemoryMB.toFixed(0)} MB</span>
        </div>
        
        <div className={`detail-item metric-${mem_status}`}>
          <strong>Memory Total (MB):</strong>
          <span>{totalMemoryMB.toFixed(0)} MB</span>
        </div>

        <div className="detail-item">
          <strong>Uptime:</strong>
          <span>{device.measurements.uptime}</span>
        </div>
      </div>
      
      {/* --- INTERFACE TABLE (NEW) --- */}
      <h2 style={{marginTop: '30px'}}>Interface Details</h2>
      <table className="device-table">
        <thead>
          <tr>
            {/* --- NEW HEADER --- */}
            <th>Status</th>
            <th>Interface Name</th>
            <th>Description</th>
            <th>Index</th>
            <th>BW In (MB/s)</th>
            <th>BW Out (MB/s)</th>
          </tr>
        </thead>
        <tbody>
          {interfaces.map(iface => (
            <tr key={iface.id}>
              {/* --- NEW CELL (with status dot) --- */}
              <td>
                <span className={`status-dot status-${iface.status}`}></span>
                {iface.status}
              </td>
              <td>{iface.ifName || 'N/A'}</td>
              <td>{iface.ifDescr || 'N/A'}</td>
              <td>{iface.ifIndex}</td>
              {/* These will show '0' until your poller is fixed! */}
              <td>{iface.bandwidth_in_mb} MB/s</td>
              <td>{iface.bandwidth_out_mb} MB/s</td>
            </tr>
          ))}
        </tbody>
      </table>

    </div>
  );
}

export default DeviceDetailsPage;