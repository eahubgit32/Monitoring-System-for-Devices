// src/MockDeviceData.js

export const mockDevices = [
  {
    "id": 1,
    "name": "Main-Router-01",
    "ip_address": "192.168.1.1",
    "status": "up", 
    "last_poll_time": "2025-11-05T09:30:01Z",
    "measurements": { 
      "cpu_percent": 25,              // <-- UPDATED
      "memory_used_percent": 60,      // <-- UPDATED
      "memory_free_mb": 12288,        // <-- NEW
      "bandwidth_in_mbps": 54.8,      // <-- NEW
      "bandwidth_out_mbps": 12.1,     // <-- NEW
      "uptime": "10d 4h 15m"
    },
    "owner": "admin"
  },
  {
    "id": 2,
    "name": "Core-Switch-A",
    "ip_address": "192.168.1.2",
    "status": "up", // Status is 'warning' because cpu_percent is high
    "last_poll_time": "2025-11-05T09:29:55Z",
    "measurements": { 
      "cpu_percent": 20,              // <-- UPDATED (high value)
      "memory_used_percent": 20,      // <-- UPDATED
      "memory_free_mb": 8192,         // <-- NEW
      "bandwidth_in_mbps": 150.2,     // <-- NEW
      "bandwidth_out_mbps": 80.5,     // <-- NEW
      "uptime": "120d 1h 0m"
    },
    "owner": "admin"
  },
  {
    "id": 3,
    "name": "Access-Point-Lobby",
    "ip_address": "192.168.1.10",
    "status": "down",
    "last_poll_time": "2025-11-05T09:25:00Z",
    "measurements": { 
      "cpu_percent": 0,               // <-- UPDATED
      "memory_used_percent": 0,       // <-- UPDATED
      "memory_free_mb": 0,            // <-- NEW
      "bandwidth_in_mbps": 0,         // <-- NEW
      "bandwidth_out_mbps": 0,        // <-- NEW
      "uptime": "0m"
    },
    "owner": "user"
  }
];