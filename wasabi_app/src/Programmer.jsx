import { useState, useRef, useEffect } from 'react'
import PlateElement from './plateElement.jsx'
import InstructionForm from './InstructionForm.jsx'
import './programmer.css'
import LegendElement from './legend.jsx'
import SaveButton from './flaskApi'
const alph = "abcdefghijklmnopqrstuvwxyz".split('')
//const staticColorLibrary = [
//  "rgb(176, 88, 88)",
//  "rgb(191, 132, 76)",
//  "rgb(196, 182, 72)",
//  "rgb(128, 135, 74)",
//  "rgb(94, 140, 102)",
//  "rgb(86, 146, 142)",
//  "rgb(98, 158, 176)",
//  "rgb(92, 116, 168)",
//  "rgb(105, 102, 153)",
//  "rgb(135, 102, 153)",
//  "rgb(153, 102, 140)",
//  "rgb(176, 122, 145)",
//  "rgb(140, 110, 88)",
//  "rgb(108, 120, 132)",
//  "rgb(132, 132, 132)",
//];
const staticColorLibrary = [
	"Red",
	"Blue",
	"Yellow",
	"DarkViolet",
	"HotPink",
	"Turquoise",
	"DarkRed",
	"LawnGreen",
	"DarkBlue",
	"DarkOrange",
]; 
function getColor() {
	const picked = staticColorLibrary.pop();
	return picked;
}
function alphNumToCoords(idString) {
	let x = parseInt(idString.slice(1), 10)
	const y = alph.indexOf(idString[0])
	if (Number.isNaN(x) || y === -1) {
		return -1
	}
	x--; // accounts for 0,0 being a1 rather than a0
	return {
		x: x,
		y: y
	}
}

function Programmer(props) {
	const initial = {
		title: "unnamed",
		version: 0,
		plateDimensions: { rows: 8, columns: 12 },
		formArray: [{ id: 0 }],
		colorLib: {},
	}

	const [experiment, setExperiment] = useState(initial)

	const setTitle = (value) => {
		setExperiment(prev => ({ ...prev, title: value }))
	}
	const setPlateDimensions = (value) => {
		setExperiment(prev => ({ ...prev, plateDimensions: value }))
	}
	const setformArray = (value) => {
		setExperiment(prev => ({ ...prev, formArray: value }))
	}
	const setColorLib = (value) => {
		setExperiment(prev => ({ ...prev, colorLib: value }))
	}

	function tmpFormArr() {
		const tmp = experiment.formArray.map(_ => _) // structured clone except it tolerates functions
		return (tmp)
	}
	let tempTitle;
	const titleInputHandler = (ev) => {
		tempTitle = ev.target.value
	}

	const titleChange = (event) => {
		if (tempTitle === undefined) return;
		setTitle(tempTitle)
	}

	const activeKeys = useRef(new Set())
	let mutableColorLib = new Map()
	const initPlateMatrix = []
	for (let row = 0; row <= experiment.plateDimensions.rows; row++) {
		const rowArray = []
		for (let column = 1; column <= experiment.plateDimensions.columns; column++) {
			rowArray.push({
				id: `${alph[row]}${column}`,
				formAttachmentData: [],
				color: '',
				colorHandler: function(currentformArray) {
					if (!this.formAttachmentData || this.formAttachmentData.length === 0) {
						this.color = ''
						return -1
					}
					// sort to avoid keying errors associated with insertion order carrying into value of the string key
					const orderKeys = this.formAttachmentData.sort((a, b) => a - b)
					const formComboStringKey = JSON.stringify(orderKeys)
					activeKeys.current.add(formComboStringKey)
					if (mutableColorLib.has(formComboStringKey)) {
						this.color = mutableColorLib.get(formComboStringKey)
						console.log(`set ${this.id} to ${this.color}`)
					} else {
						const newColor = getColor()
						mutableColorLib.set(formComboStringKey, newColor)
						orderKeys.forEach((id) => {
							currentformArray.forEach((formObject) => {
								if (formObject.id === id) {
									if (!formObject.colors) {
										formObject.colors = [newColor]
									}
									if (formObject.colors.indexOf(newColor) === -1) {
										formObject.colors.push(newColor)
									}
								}
							})
						})
						const colorLibObject = Object.fromEntries(mutableColorLib.entries())
						setColorLib(colorLibObject)
						this.color = newColor
					}
					console.log(activeKeys.current)
				},
				deleteId: function(id) {
					const forms = this.formAttachmentData
					const idIndex = forms.indexOf(id)
					if (idIndex === -1) {
						return -1
					}
					forms.splice(idIndex, 1)
				},
				hasId: function(id) {
					let outBool = false
					try {
						const hasId = (this.formAttachmentData.indexOf(id) !== -1)
						outBool = hasId
					} catch (error) {
						console.log("hasId error: ", error)
					}
					return outBool
				},
				addId: function(id) {
					this.formAttachmentData.push(id)
				}
			})
		}
		initPlateMatrix.push(rowArray)
	}
	const [plateMatrix, setPlateMatrix] = useState(initPlateMatrix)
	const orderFromTo = (formObject) => {
		const parsedFrom = alphNumToCoords(formObject.from.toLowerCase())
		const parsedTo = alphNumToCoords(formObject.to.toLowerCase())


		if (parsedFrom === -1 || parsedTo === -1) {
			return { invalid: true }

		}

		const outCoordRange = {
			lowerBound: {},
			upperBound: {}
		}

		if (parsedFrom.x > parsedTo.x) {
			outCoordRange.upperBound.x = parsedFrom.x
			outCoordRange.lowerBound.x = parsedTo.x
		} else {
			outCoordRange.upperBound.x = parsedTo.x
			outCoordRange.lowerBound.x = parsedFrom.x
		}
		if (parsedFrom.y > parsedTo.y) {
			outCoordRange.upperBound.y = parsedFrom.y
			outCoordRange.lowerBound.y = parsedTo.y
		} else {

			outCoordRange.upperBound.y = parsedTo.y
			outCoordRange.lowerBound.y = parsedFrom.y
		}

		const outOfBounds = (
			outCoordRange.lowerBound.x < 0 ||
			outCoordRange.lowerBound.y < 0 ||
			outCoordRange.upperBound.x > experiment.plateDimensions.columns ||
			outCoordRange.upperBound.y > experiment.plateDimensions.rows
		)

		if (outOfBounds) {
			return { invalid: true }
		}


		return { orderedValues: outCoordRange, invalid: false }
	}

	const getRange = (formObject) => {
		const formattedCorners = orderFromTo(formObject)
		if (formattedCorners.invalid) {
			return { invalid: true }
		}
		const lowerBound = formattedCorners.orderedValues.lowerBound
		const upperBound = formattedCorners.orderedValues.upperBound
		const area = (upperBound.x - lowerBound.x) * (upperBound.y - lowerBound.y)
		const plateMatrix_subRange = []
		for (let row = lowerBound.y; row <= upperBound.y; row++) {
			plateMatrix_subRange[row] = []
			for (let column = lowerBound.x; column <= upperBound.x; column++) {
				plateMatrix_subRange[row][column] = plateMatrix[row][column]
			}
		}
		return { range: plateMatrix_subRange, area: area, invalid: false };
	}

	const rangeHandler = (formObject) => {
		activeKeys.current.clear()
		const mutablePlateMatrix = plateMatrix.map((row) => ([...row]))
		const formattedRange = getRange(formObject)
		if (formattedRange.invalid) {
			return -1
		}
		const cornerRange = formattedRange.range
		formObject.area = cornerRange.area
		let colorHandlerResponse;
		mutablePlateMatrix.forEach((rowObject, row) => {
			rowObject.forEach((wellElement, column) => {
				const subRange_row = cornerRange[row]  
				let cornerRange_wellElement = false
				wellElement.deleteId(formObject.id)
				if (subRange_row) {
					cornerRange_wellElement = subRange_row[column] != undefined
					if (cornerRange_wellElement && !wellElement.hasId(formObject.id)) {
						wellElement.addId(formObject.id)
					}
				}
				colorHandlerResponse = wellElement.colorHandler(experiment.formArray)
			})
		})
		if (colorHandlerResponse === -1) {
			return
		}
		setPlateMatrix(mutablePlateMatrix)
	}

	const modifyFormArray = (formObject) => {
		if (experiment.formArray[formObject.id]) {
			const tmp = tmpFormArr()
			tmp[formObject.id] = formObject
			setformArray([...tmp])
		} else {
			setformArray([...experiment.formArray, formObject])
		}
	}

	const addEmptyForm = () => {
		const latestForm = experiment.formArray[experiment.formArray.length - 1]
		const emptyForm = {
			id: (latestForm.id + 1)
		}
		modifyFormArray(emptyForm)
		console.log(activeKeys)
	}

	const deleteForm = (event) => {
		const id = parseInt(event.target.id)
		const shortenedFormArray = tmpFormArr().filter((form) => {
			console.log(form.id)
			const isntForm = form.id !== id
			console.log('filtering')
			console.log(isntForm)
			return isntForm
		})
		console.log(shortenedFormArray)
		setformArray(shortenedFormArray)
	}


	const keydownHandler = (event) => {
		console.log('keydown event ')
		if (
			["Enter", "Escape"].includes(event.key)) {
			event.target.blur()
		}
	}

	const loading = useRef(true)

	if (loading.current == "done") {
		loading.current = false
		setExperiment(props.experiment)
		console.log(props.experiment)
	}
	if (loading.current == true) {
		loading.current = "done"
	}
	console.log(experiment)

	return (
		<div id="experiment">
			<div id="forms">
				<input
					type="text"
					name="experimentTitle"
					defaultValue = {props.experiment.title}
					onInput={titleInputHandler}
					onBlur={titleChange}
					onKeyDown={keydownHandler}
					placeholder="insert title"
				/>
				<SaveButton version = {props.experiment.version} experiment={experiment} setExperiment={setExperiment} />
				<table>
					<thead>
						<tr>
							<th> reagent </th>
							<th> method </th>
							<th> coordinates </th>
						</tr>
					</thead>
					<tbody>
						{experiment.formArray.map((form) => (
							<InstructionForm key={form.id} className="instructionForm"
								constructor={experiment.formArray[form.id]}
								id={form.id}
								rangeHandler={rangeHandler}
								modifyFormArray={modifyFormArray}
								deleteForm={deleteForm}
								keydownHandler={keydownHandler}
							/>
						))}
					</tbody>
				</table>
				<button onClick={addEmptyForm}> add form </button>
				<LegendElement activeKeys={activeKeys} experiment = {experiment} colorLib={experiment.colorLib} />
			</div>
			<div id="visualElements">
				<PlateElement plateMatrix={plateMatrix} />
			</div>
		</div>
	)
}

export default Programmer
