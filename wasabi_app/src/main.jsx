import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { ExperimentContextProvider } from './ExperimentContextProvider.jsx'
import { BrowserRouter } from 'react-router-dom';



createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ExperimentContextProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ExperimentContextProvider>
  </StrictMode>,
)
