import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import Programmer from './Programmer.jsx'
import Testenv  from './test.jsx' 
createRoot(document.getElementById('root')).render(
  <StrictMode>
 <Programmer />
  </StrictMode>,
)
