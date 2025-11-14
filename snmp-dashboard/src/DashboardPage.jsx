// src/DashboardPage.jsx - MODIFIED VERSION

import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import DeviceTable from './DeviceTable.jsx';
import { deviceService } from './api/deviceService.js'; 
import './DashboardPage.css';
import { useUser } from './UserContext.jsx';
// We no longer need the modal
// import ConfirmDeleteModal from './ConfirmDeleteModal.jsx'; 

function DashboardPage() {
  const [fetchedDevices, setFetchedDevices] = useState([]); 
  const [searchTerm, setSearchTerm] = useState("");
  
  // --- STATE FOR PERSISTENCE FEATURE (Unchanged) ---
  const [selectedDeviceIds, setSelectedDeviceIds] = useState([]);
  const [pendingSelectedIds, setPendingSelectedIds] = useState([]);
  const [isPersistentFilterOn, setIsPersistentFilterOn] = useState(false); 
  const [isPreferenceLoading, setIsPreferenceLoading] = useState(true); 
  
  const [isLoading, setIsLoading] = useState(true); 
  const [error, setError] = useState(null);

  // --- STATE FOR "SHOW HIDDEN" (REMOVED) ---
  // const [showHidden, setShowHidden] = useState(false);

  const { user } = useUser();
  const role = user?.role;
  const userId = user?.id;
  const isAdmin = role === 'admin'; // We can keep this for other potential features

  const dashboardTitle = role === 'admin' 
    ? "Network Device Dashboard (Admin View)" 
    : "My Devices (User View)";

// --- DATA FETCHING (WITH POLLING) ---
// (This section is correct and unchanged)
  // 1. Move your fetch logic into its own function
  const fetchDevices = async () => {
    if (!userId) return; // Don't fetch if no user

    try {
      // Set loading only if it's the *first* load
      if (fetchedDevices.length === 0) {
        setIsLoading(true);
      }
      setError(null);
      
      const data = await deviceService.getAllDevices(false);
      
      const devicesArray = Array.isArray(data.devices) ? data.devices : [];
      setFetchedDevices(devicesArray);
      
    } catch (e) {
      setError(e.message);
      setFetchedDevices([]);
    } finally {
      // Always turn off loading, even on subsequent polls
      setIsLoading(false);
    }
  };

  // 2. Modify your useEffect to use an interval
  useEffect(() => {
    // Fetch data immediately when the page loads
    fetchDevices(); 

    // Then, set up an interval to re-fetch 1 minute
    const pollInterval = setInterval(() => {
      fetchDevices();
    }, 100000);

    // This is CRITICAL: a "cleanup function"
    // It runs when you leave the page to stop the interval
    return () => {
      clearInterval(pollInterval);
    };

  }, [userId]); // <-- This effect still only *runs* when userId changes

  // --- PERSISTENCE LOADER (THIS IS THE FIXED SECTION) ---
  useEffect(() => {
    // --- THIS IS THE FIX ---
    // We only check for userId. We *want* this to run even if
    // fetchedDevices.length is 0, so it can set loading to false.
    if (!userId) return;

    const loadPreferences = async () => {
      try {
        setIsPreferenceLoading(true);
        const data = await deviceService.loadFilterPreferences(); 
        const ids = data.selected_device_ids
            ? data.selected_device_ids.split(',').map(id => parseInt(id.trim()))
            : [];
        
        // This check is fine, because fetchedDevices is available from the other hook
        const validIds = ids.filter(id => fetchedDevices.some(d => d.id === id));
        
        setSelectedDeviceIds(validIds);
        setPendingSelectedIds(validIds); 
        setIsPersistentFilterOn(data.is_filter_active);
      } catch (e) {
        setSelectedDeviceIds([]);
        setPendingSelectedIds([]);
        setIsPersistentFilterOn(false);
      } finally {
        // This 'finally' block will NOW ALWAYS RUN, fixing the bug
        setIsPreferenceLoading(false);
      }
    };
    loadPreferences();
  }, [userId, fetchedDevices.length]); // Dependency array is unchanged and correct

  
  // --- HANDLERS (Unchanged) ---
  const handleToggleFilter = (e) => {
    setIsPersistentFilterOn(e.target.checked);
  };
  
  const handleDeviceSelection = (deviceId) => {
    setPendingSelectedIds(prevIds => 
      prevIds.includes(deviceId)
        ? prevIds.filter(id => id !== deviceId)
        : [...prevIds, deviceId]
    );
  };
  
  const handleApplyFilter = async () => {
    if (!userId || isLoading || isPreferenceLoading) return; 
    const idsString = pendingSelectedIds.join(',');
    const stateToSave = {
        selected_device_ids: idsString,
        is_filter_active: isPersistentFilterOn,
    };
    try {
      await deviceService.saveFilterPreferences(stateToSave);
      setSelectedDeviceIds(pendingSelectedIds); 
    } catch (e) {
        setError(e.message);
    }
  };

  // --- "SHOW HIDDEN" HANDLER (REMOVED) ---
  // const handleShowHiddenToggle = (e) => {
  //   setShowHidden(e.target.checked);
  // };

  // --- DELETE HANDLER (REMOVED) ---


  // --- CORE FILTER LOGIC (Unchanged) ---
  const finalDeviceList = useMemo(() => {
    let list = fetchedDevices;
    
    if (isPersistentFilterOn && selectedDeviceIds.length > 0) {
      list = list.filter(device => selectedDeviceIds.includes(device.id));
    }

    if (searchTerm) {
      list = list.filter(device => 
        device.name && device.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    return list;
  }, [fetchedDevices, selectedDeviceIds, isPersistentFilterOn, searchTerm]);

  // --- RENDER LOGIC ---
  // This check is now safe, because isPreferenceLoading will be set to false
  if (isLoading || isPreferenceLoading) {
    return <div className="loading-spinner">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error-message">Error: {error}</div>;
  }
  
  const totalScopeCount = fetchedDevices.length;
  const currentDisplayCount = finalDeviceList.length;
  
  let contextIndicatorText = `Displaying all ${totalScopeCount} devices in your scope.`;
  if (isPersistentFilterOn && totalScopeCount > 0) {
    contextIndicatorText = `Filtered: Displaying ${currentDisplayCount} out of ${totalScopeCount} total devices in your scope.`;
  }
  
return (
    <div className="dashboard-container">
      <h1>{dashboardTitle}</h1>
      
      <p className="context-indicator">{contextIndicatorText}</p> 

      {/* --- THIS IS THE MODIFIED SECTION --- */}
      <div className="dashboard-header-bar">
          <div className="dashboard-actions">
            <Link to="/add-device" className="add-device-button">
              + Add New Device
            </Link>
          </div>
          
          {/* We move the search bar INSIDE here */}
          <div className="filter-controls">
            
            {/* The search bar now lives here */}
            <input
              type="text"
              placeholder="Filter by device name..."
              className="search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />

            {/* The other filter controls */}
            <label>
                <input 
                    type="checkbox"
                    checked={isPersistentFilterOn}
                    onChange={handleToggleFilter}
                />
                Show Only Filtered
            </label>
            
            <button 
              className="apply-filter-button" 
              onClick={handleApplyFilter}>
                  Apply/Save Filter ({pendingSelectedIds.length})
            </button>
          </div>
      </div>
      
      {finalDeviceList.length === 0 && searchTerm === "" && totalScopeCount > 0 ? (
          <p className="no-devices-message">No devices found in your scope.</p>
      ) : (
          <DeviceTable 
            devices={finalDeviceList}
            // The onDelete prop has been REMOVED
            onSelect={handleDeviceSelection} 
            // All other props are removed
            selectedIds={pendingSelectedIds}
            isFiltering={isPersistentFilterOn}
          />
      )}
      
      {/* The Modal component is no longer rendered */}
      
    </div>
  );
}
  
export default DashboardPage;