import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  // CRITICAL FIX: This tells Vite to prefix all asset paths (JS, CSS) 
  // in the generated index.html with '/static/'.
  base: '/static/', 
  plugins: [react()],
})
