import { useState, useRef, useEffect, useContext } from 'react'
import PlateElement from './plate_element.jsx'
import InstructionForm from './InstructionForm.jsx'
import { v4 as uuidv4 } from 'uuid';
import SaveButton from './SaveButton.jsx';
import './css/Programmer.css'
import { control_call } from '@src/backendConfig.jsx';
import { AppGlobalContext, default_form } from '@src/AppGlobalContext.jsx';

function Programmer(props) {

  const { experiment, set_experiment } = useContext(AppGlobalContext)

  const modify_experiment = (key, value) => {
    set_experiment(previous_value => ({ ...previous_value, [key]: value }))
  }
  const setTitle = (value) => {
    modify_experiment("title", value)
  }
  const setPlateDimensions = (value) => {
    modify_experiment("plateDimensions", value)
  }
  const setForms = (value) => {
    modify_experiment("forms", value)
  }

  const addEmptyForm = () => {
    const current_form_count = Object.keys(experiment.forms).length
    const tmp = structuredClone(experiment)
    const empty_form = {...default_form, id: uuidv4(), index:current_form_count}
    if (current_form_count == 0) {
      empty_form.id = "form_0"
    } else {
      tmp.forms[experiment.selected_id].is_selected = false
    }
    tmp.forms[empty_form.id] = empty_form
    tmp.selected_id = empty_form.id
    set_experiment(tmp)
  }

  const deleteForm = (event) => {
    const target_id = event.target.id
    const { [target_id]: _, ...new_forms_object } = experiment.forms;
    setForms(new_forms_object)
  }

  const keydownHandler = (event) => {
    if (["Enter", "Escape"].includes(event.key)) {
      event.target.blur()
    }
  }


  return (
    <div id="experiment">
      <div id="instruction-input">
        <div className="title-row">
          <input
            type="text"
            key={experiment.title}
            name="experimentTitle"
            defaultValue={experiment.title}
            onBlur={(event) => setTitle(event.target.value)}
            onKeyDown={keydownHandler}
            placeholder="experiment title"
          />
          <span className="version-label">v{experiment.version}</span>
        </div>
        <div className="form-actions">
          <SaveButton />
        </div>
        <div className="forms">
          {Object.keys(experiment.forms).map((form_id) => (
            <InstructionForm
              id={form_id}
              key={form_id}
            />
          ))}
        </div>
        <button className="add-form-btn" onClick={addEmptyForm}>+ add instruction</button>
      </div>
      <div id="visualElements">
        <PlateElement/>
      </div>
    </div>
  )
}
export default Programmer
