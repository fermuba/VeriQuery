import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { MsalAuthProvider } from './auth'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <MsalAuthProvider>
        <App />
      </MsalAuthProvider>
    </BrowserRouter>
  </StrictMode>
)
