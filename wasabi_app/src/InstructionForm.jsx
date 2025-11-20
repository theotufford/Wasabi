import { useState } from 'react'
import { useEffect } from 'react';
import DdSelect from './dropDownElement.jsx'
import './instructionForm.css'

function getMethodForm(formObject) {
  const handleMethodInput = (event) => {
    const key = event.target.name
    const value = event.target.value
    formObject.methodObject[key] = value
  }

  const constantMethod = (
    <>
    <input
      type="text" 
      name="constantVolume" 
      placeholder = "volume"
    onChange = {handleMethodInput}
    />
    </>
  )
  const gradientMethod = (
    <>
    <select
      name = "gradientDirection"
      onChange = {handleMethodInput}
    >
      <option value="right">right</option>
      <option value="left">left</option>
      <option value="down">down</option>
      <option value="up">up</option>
    </select>
    <input 
      type="text"
      name="initialVolume"
      placeholder = "initial volume"
      onChange = {handleMethodInput}
    />
    <input 
      type="text"
      name="increment"
      placeholder = "increment"
      onChange = {handleMethodInput}
    />
    </>
  )
  const methods = {
    constant:constantMethod,
    gradient:gradientMethod
  }
  return (methods[formObject.method])
}

function InstructionForm(props) {
  let initialState = {
    id:0,
    reagent:"empty",
    method:"constant",
    methodObject:{},
    from:"", to:"",
    colors: []
  }
  initialState = {...initialState, ...props}
  const [formObject, setFormValues] = useState(initialState)

  useEffect(() => {
    props.rangeHandler(formObject)
  }, [formObject.from, formObject.to])

  useEffect(() => {
    props.modifyFormArray(formObject)
  }, [formObject])


  const handleFormUpdate = (event) => {
    const update = {}
    update[event.target.name] = event.target.value
    setFormValues(prev => ({...prev, ...update}))
  }


	const keydownHandler = props.keydownHandler


  return (
    <tr>
		<td><button id = {props.id} onClick = {props.deleteForm}></button></td>
		<td>
			<input 
				type="text"
				name="reagent"
				placeholder = "input reagent"
				value = {props.reagent}
				onKeyDown = {keydownHandler}
				onBlur = {handleFormUpdate}
			/>
			<button type="submit" style = {{display:"none"}} >log reagent</button>
		</td>

		<td>
			<select
				type="text"
				name="method"
				placeholder = "pickMethod"
				selected = {props.method} 
				onChange = {handleFormUpdate} 
			>
				<option value="constant">constant</option>
				<option value="gradient">gradient</option>
			</select>
			<div className = "method">
				{getMethodForm(formObject)}
			</div>
		</td>

		<td>
			<div className="fromTo">
				<input 
					type="text"
					name="from"
					placeholder = "from"
					value = {props.from} 
					onBlur = {handleFormUpdate}
					onKeyDown = {keydownHandler}
				/>
				<input 
					type="text"
					name="to"
					value = {props.to} 
					placeholder = "to"
					onBlur = {handleFormUpdate}
					onKeyDown = {keydownHandler}
				/>
			</div>
		</td>

    </tr>
  )
}
export default InstructionForm
