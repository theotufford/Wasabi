import { useState, useRef, useEffect  } from 'react'
import Programmer from './Programmer.jsx'

function App() {

  const [windowSelect, setSelectedWindow] = useState(<Programmer/>)

  return (
    <>
      {windowSelect}
    </>
  )
}

export default App
