import { useState, useRef, useEffect  } from 'react'
import {socket, apiCall} from './backendConfig.jsx'


const load_experiment = () => {
	const response = apiCall({
		route:"fetchExperiment",
		body:{
			title:"empty",
			version: 2 
		}
	})
		.then(response => JSON.parse(response.data))
		.then(data => console.log(data)) 
}

const list_experiments = () => {
	const response = apiCall({
		route:"dbDump"
	}) 
		.then(response => console.log(response.data))
}

const TestButton = () => {
	return (
		<>
		<button onClick = {load_experiment}>load button</button>
		<button onClick = {list_experiments}>dump button</button>
		</>
	)
}

export default TestButton
