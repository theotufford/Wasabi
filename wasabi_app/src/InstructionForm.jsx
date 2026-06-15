import { useState } from 'react'
import { useEffect } from 'react';
import './instructionForm.css'
const initial_form_state = { 
  id: crypto.randomUUID(),
  reagent: "empty",
  method: "constant",
  methodObject: {},
  from: "", to: "",
  colors: []
}

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
        placeholder="volume µL"
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
        placeholder="initial volume µL"
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
  const [formObject, setFormValues] = useState(() => (props.constructor))

  useEffect(() => {
    //props.rangeHandler(formObject)
  }, [formObject.from, formObject.to])

  useEffect(() => {
    props.modifyForms(formObject)
  }, [formObject])

  const handleFormUpdate = (event) => {
    const update = {}
    update[event.target.name] = event.target.value
    setFormValues(prev => ({ ...prev, ...update }))
  }
  const keydownHandler = props.keydownHandler

  return (
    <tr>
      <td className="row-num">{props.rowIndex}</td>
      <td>
        <input
          type="text"
          name="reagent"
          placeholder="reagent"
          defaultValue={formObject.reagent}
          onKeyDown={keydownHandler}
          onBlur={handleFormUpdate}
        />
        <button type="submit" style={{ display: "none" }}>log reagent</button>
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
      </td>
      <td>
        <div className="method-inputs">
          {getMethodForm(formObject)}
        </div>
      </td>
      <td>
        <div className="from-to">
          <input
            type="text"
            name="from"
            placeholder="a1"
            defaultValue={formObject.from}
            onBlur={handleFormUpdate}
            onKeyDown={keydownHandler}
          />
          <input
            type="text"
            name="to"
            defaultValue={formObject.to}
            placeholder="h12"
            onBlur={handleFormUpdate}
            onKeyDown={keydownHandler}
          />
        </div>
      </td>
      <td>
        <button id={props.id} onClick={props.deleteForm} className="btn-danger">✕</button>
      </td>
    </tr>
  )
}
export default InstructionForm
