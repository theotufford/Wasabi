import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { AppGlobalContextProvider } from './AppGlobalContextProvider.jsx'
import { BrowserRouter } from 'react-router-dom';



createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AppGlobalContextProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AppGlobalContextProvider>
  </StrictMode>,
)
