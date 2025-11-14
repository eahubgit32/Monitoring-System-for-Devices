// src/DeviceTable.jsx - MODIFIED VERSION

import React from 'react';
import { Link } from 'react-router-dom'; // Keep this for the 'Name' link
import './DeviceTable.css';

// 'onDelete' prop is removed
function DeviceTable({ devices, onSelect, selectedIds, isFiltering }) {

  if (devices.length === 0) {
    return <p>No devices found.</p>;
  }

  // Add the base URL for your Django Admin
  const djangoAdminBaseUrl = 'http://localhost:8000';

  return (
    <table className="device-table">
      <thead>
        <tr>
          <th>{isFiltering ? 'Selected' : 'Select'}</th> 
          <th>Status</th>
          <th>Name</th>
          <th>IP Address</th>
          <th>CPU</th>
          <th>Mem (Used) MB</th>
          <th>Mem (Free) MB</th>
          <th>Mem (Total) MB</th>
          {/* BW In and Out <th> elements are REMOVED */}
          <th>Actions</th>
        </tr>
      </thead>
      
      <tbody>
        {devices.map((device) => {
          
          // --- (All this metric logic is correct and unchanged) ---
          const cpu_value = device.measurements.cpu?.value || 0;
          const cpu_status = device.measurements.cpu?.status || 'good';
          const usedBytes = device.measurements.memory?.used_bytes || 0;
          const freeBytes = device.measurements.memory?.free_bytes || 0;
          const mem_status = device.measurements.memory?.status || 'good';
          const bytesPerMB = 1024 * 1024;
          const usedMemoryMB = usedBytes / bytesPerMB;
          const freeMemoryMB = freeBytes / bytesPerMB;
          const totalMemoryMB = (usedBytes + freeBytes) / bytesPerMB;
          const isDeviceSelected = selectedIds.includes(device.id);

          return (
            <tr key={device.id}>
              {/* Selection cell (Unchanged) */}
              <td className="selection-cell">
                <input
                    type="checkbox"
                    checked={isDeviceSelected}
                    onChange={() => onSelect(device.id)} 
                />
              </td>
              
              {/* Device Status (up/down) (Unchanged) */}
              <td>
                <span className={`status-dot status-${device.status}`}></span>
                {device.status}
              </td>
              
              {/* "Name" cell still links to your React Details Page */}
              <td>
                <Link to={`/device/${device.id}`}>{device.name}</Link>
              </td>
              <td>{device.ip_address}</td>

              {/* Metric Cells (Unchanged) */}
              <td className={`metric-${cpu_status}`}>
                {cpu_value}%
              </td>
              <td className={`metric-${mem_status}`}>
                {usedMemoryMB.toFixed(0)} MB
              </td>
              <td className={`metric-${mem_status}`}>
                {freeMemoryMB.toFixed(0)} MB
              </td>
              <td className={`metric-${mem_status}`}>
                {totalMemoryMB.toFixed(0)} MB
              </td>
              
              {/* BW In and Out <td> elements are REMOVED */}

              {/* "ACTIONS" CELL (Unchanged) */}
              <td className="actions-cell">
                <a 
                  href={`${djangoAdminBaseUrl}/admin/monitoring/device/${device.id}/change/`}
                  className="action-button edit-button"
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  Edit
                </a>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export default DeviceTable;