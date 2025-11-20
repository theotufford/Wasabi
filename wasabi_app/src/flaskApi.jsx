import { useEffect, useRef, useState } from 'react';
import { socket, apiCall } from './backendConfig.jsx';
const SaveButton = (props) => {

	const autoSave = useRef(true)
	const save = (experiment) => {
		console.log('autosave = ', autoSave)
			socket.emit('saveExperiment', {...experiment, autoSave : autoSave.current})
	}

	let experiment = props.experiment
	const explicitSave = () => {
		autoSave.current = false
		save(experiment)
	}
	useEffect(() => { //save on change 
		autoSave.current = true
		save(experiment)

	}, [experiment])
	return (
		<button onClick={explicitSave}>Save version {experiment.version}</button>
	)
}
export default SaveButton
