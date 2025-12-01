import { useState, useRef, useEffect  } from 'react'
import {apiCall,dataStream} from './backendConfig.jsx'
import TestButton from './browserFrame.jsx'


function Controller(){
	// TODO:
	// live position
	// home button
	// run button
	// reagent table
	// data stream
	const [serialMessage, setSerialMessage] = useState(".....")
	useEffect(() => {
		console.log(dataStream)
		dataStream.onmessage = (e) => {
			setSerialMessage(e.data)
		}
	}, [])
	
	return (
	<div>
			<h1>{serialMessage}</h1>
	</div>
	)
}
export default Controller
