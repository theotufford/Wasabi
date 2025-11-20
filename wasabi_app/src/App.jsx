import { useState, useRef, useEffect  } from 'react'
import Programmer from './Programmer.jsx'
import {socket, apiCall} from './backendConfig.jsx'
import TestButton from './browserFrame.jsx'

function App() {
	const experimentTemplate = {
		title:"unnamed",
		version:0,
		plateDimensions:{ rows:8, columns:12 },
		formArray:[{ id:0 }],
		colorMap:new Map(),
	}


	const [experiment, setExperiment] = useState(experimentTemplate)
  const [windowSelect, setSelectedWindow] = useState(
		<Programmer 
		experiment = {experiment}
		setExperiment = {setExperiment}
		/>)

	console.log("windowSelect is now: ", windowSelect)
  return (
    <>
		<TestButton/>
		{windowSelect}
    </>
  )
}

export default App
