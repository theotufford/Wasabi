import { useState, useRef, useEffect } from 'react'
import Programmer from './Programmer.jsx'
import BrowserElement from './browserFrame.jsx'
import Controller from './controller.jsx'

function App() {
	const experimentTemplate = {
		title: "unnamed",
		version: 0,
		plateDimensions: { rows: 8, columns: 12 },
		formArray: [{ id: 0 }],
		colorLib: {},
	}

	const experiment = useRef(experimentTemplate)

	const setExperiment = (value) => {
		experiment.current = value
	}

	const goToController = () => {
		setSelectedWindow(
			<Controller
				experiment={experiment.current}
				goToEditor={goToEditor}
				goToSearch={goToSearch}
			/>
		)
	}

	const goToSearch = () => {
		setSelectedWindow(
			<BrowserElement
				experiment={experiment.current}
				setExperiment={setExperiment}
				goToEditor={goToEditor}
				goToController={goToController}
			/>
		)
	}

	const goToEditor = () => {
		setSelectedWindow(
			<Programmer
				experiment={experiment.current}
				goToSearch={goToSearch}
				goToController={goToController}
			/>)
	}
// session should hold windowSelect 

	const [windowSelect, setSelectedWindow] = useState(
		<div>
			<BrowserElement
				experiment={experiment}
				setExperiment={setExperiment}
				goToEditor={goToEditor}
				goToController={goToController}
			/>
		</div>
	)

	console.log("windowSelect is now: ", windowSelect)
	return (
		<>
			{windowSelect}
		</>
	)
}
export default App
