// src/api/deviceService.js

const API_BASE_URL = 'http://localhost:8000/api';

// --- UTILITY FUNCTIONS ---
const getCookie = (name) => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

const getAuthHeaders = () => {
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        throw new Error("CSRF token is missing. Please ensure you are logged in.");
    }
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken, 
    };
}


async function handleResponse(response) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorDetail = errorData.detail || errorData.non_field_errors || `HTTP Error! Status: ${response.status}`;
    const errorMessage = errorDetail;
    console.error('API Error:', errorMessage);
    throw new Error(errorMessage);
  }
  return response.json();
}

/**
 * API SERVICE
 */
export const deviceService = {
  
  getAllDevices: async (includeInactive = false) => {
    // 1. Create a URL object
    const url = new URL(`${API_BASE_URL}/devices/`);

    // 2. Add the query parameter *only if* it's true
    if (includeInactive) {
      url.searchParams.append('include_inactive', 'true');
    }

    // 3. Fetch using the URL string
    const response = await fetch(url.toString(), {
      credentials: 'include'
    });
    
    const data = await handleResponse(response);
    return { devices: data }; 
  },
  
  // ... getDeviceById and getDeviceModels omitted for brevity ...

  getDeviceById: async (id) => {
    console.log(`API_SERVICE: Fetching device ${id} from REAL API...`);
    const response = await fetch(`${API_BASE_URL}/devices/${id}/`,{credentials: 'include'});
    const data = await handleResponse(response);
    return { device: data }; 
  },

  getDeviceModels: async () => {
    console.log("API_SERVICE: Fetching all device models...");
    const response = await fetch(`${API_BASE_URL}/models/`,{
    credentials: 'include'
    });
    return await handleResponse(response); 
  },

  getDeviceModels: async () => {
    const response = await fetch(`${API_BASE_URL}/models/`,{
    credentials: 'include'
    });
    return await handleResponse(response); 
  },

  /**
   * Adds a new device to the REAL backend.
   */
  addDevice: async (deviceData) => { // Removed 'owner' from signature
    
    // FIX 4: CRITICAL SECURITY FIX: Remove user_id from the payload.
    // The backend (perform_create) must set the user_id, not the frontend.
    const payload = {
      name: deviceData.hostname, // Django expects 'name' (maps to model's 'hostname')
      ip_address: deviceData.ipAddress,
      model_id: deviceData.modelId,
      // user_id MUST NOT be here.
    };
    
    const response = await fetch(`${API_BASE_URL}/devices/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
      credentials: 'include' 
    });
    
    const data = await handleResponse(response);
    return { device: data };
  },

  // --- THIS IS THE NEW FUNCTION ---
// --- THIS IS THE NEW FUNCTION ---
  getDeviceInterfaces: async (deviceId) => {
    console.log(`API_SERVICE: Fetching interfaces for device ${deviceId}...`);
    const response = await fetch(`${API_BASE_URL}/devices/${deviceId}/interfaces/`, {
      credentials: 'include'
    });
    // We just return the data array from handleResponse
    return await handleResponse(response);
  },

  /**
   * Deletes a device from the REAL backend.
   */
  //deleteDevice: async (id) => {
    //console.log(`API_SERVICE: Deleting device ${id} from REAL API...`);
    
    //const response = await fetch(`${API_BASE_URL}/devices/${id}/`, {
      //method: 'DELETE',
     // headers: getAuthHeaders(),
      //credentials: 'include'
    //});
    
   // if (!response.ok) {
     // throw new Error(`HTTP Error! Status: ${response.status}`);
    //}
    //return { success: true };
  //},

  /**
   * Hides a device from the dashboard. (Soft Delete)
   */
  //hideDevice: async (id) => {
  //  console.log(`API_SERVICE: Hiding (soft deleting) device ${id}...`);

   // const payload = {
    //  is_active: false // This is the only change we send
    //};

    //const response = await fetch(`${API_BASE_URL}/devices/${id}/`, {
      //method: 'PATCH',
     // headers: getAuthHeaders(),
     // body: JSON.stringify(payload),
     // credentials: 'include'
    //});

    //return await handleResponse(response);
  //},

  /**
   * Updates a device's name in the REAL backend.
   */
  updateDevice: async (id, newName) => {
    console.log(`API_SERVICE: Updating device ${id} with PATCH...`);
    
    const payload = {
      hostname: newName, // <--- Correct field name for Django model
    };

    const response = await fetch(`${API_BASE_URL}/devices/${id}/`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
      credentials: 'include'
    });
    
    const data = await handleResponse(response);
    return { device: data };
  },

  loadFilterPreferences: async () => {
    console.log("API_SERVICE: Loading user preferences...");
    // We rely on the backend's get_object to find the current user's preference
    const response = await fetch(`${API_BASE_URL}/preferences/`, { credentials: 'include' });
    const data = await handleResponse(response);
    return data; 
  },


  saveFilterPreferences: async (preferenceData) => {
    console.log("API_SERVICE: Saving user preferences...");
    
    // We send a PATCH request to update the existing preference object
    const response = await fetch(`${API_BASE_URL}/preferences/`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(preferenceData),
      credentials: 'include' 
    });
    return await handleResponse(response);
  },



  unhideDevice: async (id) => {
    console.log(`API_SERVICE: Un-hiding (soft activating) device ${id}...`);

    const payload = {
      is_active: true // This is the only change we send
    };

    const response = await fetch(`${API_BASE_URL}/devices/${id}/`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
      credentials: 'include'
    });

    return await handleResponse(response);
  },
};