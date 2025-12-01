import { useEffect, useRef, useState } from 'react';
import  apiCall  from './backendConfig.jsx';
const SaveButton = (props) => {
	const autoSave = useRef(true)
	const save = (experiment) => {
		console.log('autosave = ', autoSave)
		experiment.autosave = autoSave.current
		console.log('color map save : ', experiment.colorMap)
		apiCall({
			route:"saveExperiment",
			body:experiment
		})
	}
	const experiment = props.experiment
	const setExperiment = props.setExperiment
	const version = props.version
	const explicitSave = () => {
		autoSave.current = false
		setExperiment({...experiment, version:(experiment.version + 1)})
		save(experiment)
	}
	useEffect(() => { //save on change 
		autoSave.current = true
		save(experiment)

	}, [experiment])
	return (
		<button onClick={explicitSave}>Save</button>
	)
}
export default SaveButton
