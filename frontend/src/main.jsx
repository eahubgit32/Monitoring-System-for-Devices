import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import DiscoverDevice from './DiscoverDevice.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <DiscoverDevice />
  </StrictMode>,
)
