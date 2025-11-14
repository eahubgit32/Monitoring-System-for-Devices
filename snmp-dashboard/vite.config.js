import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // This is still needed
    port: 5173,
    
    // --- ADD THIS BLOCK ---
    // This tells Vite to trust the 'dev.local' hostname
    allowedHosts: [
      'dev.local'
    ]
    // ----------------------
  }
})