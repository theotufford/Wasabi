import { useState } from 'react'
import { useEffect } from 'react';
import './instructionForm.css'

function getMethodForm(formObject) {
	const handleMethodInput = (event) => {
		const key = event.target.name
		const value = event.target.value
		formObject.methodObject[key] = value
	}

	const initial = formObject.methodObject

	const constantMethod = (
		<>
			<input
				type="text"
				name="constantVolume"
				placeholder="volume"
				defaultValue={initial?.constantVolume}
				onChange={handleMethodInput}
			/>
		</>
	)
	const gradientMethod = (
		<>
			<select
				name="gradientDirection"
				onChange={handleMethodInput}
			>
				<option value="right">right</option>
				<option value="left">left</option>
				<option value="down">down</option>
				<option value="up">up</option>
			</select>
			<input
				type="text"
				name="initialVolume"
				placeholder="initial volume"
				defaultValue={initial?.initialVolume}
				onChange={handleMethodInput}
			/>
			<input
				type="text"
				name="increment"
				placeholder="increment"
				defaultValue={initial?.increment}
				onChange={handleMethodInput}
			/>
		</>
	)
	const methods = {
		constant: constantMethod,
		gradient: gradientMethod
	}
	return (methods[formObject.method])
}
function InstructionForm(props) {
	let initialState = {
		id: 0,
		reagent: "empty",
		method: "constant",
		methodObject: {},
		from: "", to: "",
		colors: []
	}
	const [formObject, setFormValues] = useState(() => ({ ...initialState, ...props.constructor }))
	useEffect(() => {
		props.rangeHandler(formObject)
	}, [formObject.from, formObject.to])
	useEffect(() => {
		props.modifyFormArray(formObject)
	}, [formObject])
	const handleFormUpdate = (event) => {
		const update = {}
		console.log('changed ', { ...update })
		update[event.target.name] = event.target.value
		setFormValues(prev => ({ ...prev, ...update }))
	}
	const keydownHandler = props.keydownHandler
	return (
		<tr>
			<td>
				<input
					type="text"
					name="reagent"
					placeholder="input reagent"
					defaultValue={formObject.reagent}
					onKeyDown={keydownHandler}
					onBlur={handleFormUpdate}
				/>
				<button type="submit" style={{ display: "none" }} >log reagent</button>
			</td>

			<td>
				<select
					type="text"
					name="method"
					placeholder="pickMethod"
					selected={formObject.method}
					onChange={handleFormUpdate}
				>
					<option value="constant">constant</option>
					<option value="gradient">gradient</option>
				</select>
				<div className="method">
					{getMethodForm(formObject)}
				</div>
			</td>

			<td>
				<div className="fromTo">
					<input
						type="text"
						name="from"
						placeholder="from"
						defaultValue={formObject.from}
						onBlur={handleFormUpdate}
						onKeyDown={keydownHandler}
					/>
					<input
						type="text"
						name="to"
						defaultValue={formObject.to}
						placeholder="to"
						onBlur={handleFormUpdate}
						onKeyDown={keydownHandler}
					/>
				</div>
			</td>
			<button id={props.id} onClick={props.deleteForm}>delete</button>
		</tr>
	)
}
export default InstructionForm
