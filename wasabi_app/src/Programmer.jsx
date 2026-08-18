import { useState, useRef, useEffect, useContext } from 'react'
import PlateElement from './plate_element.jsx'
import InstructionForm from './InstructionForm.jsx'
import { v4 as uuidv4 } from 'uuid';
import SaveButton from './SaveButton.jsx';
import './Programmer.css'
import { control_call } from './backendConfig.jsx';
import { ExperimentContext } from './ExperimentContext.jsx';
import ComboTree from './color_combo_tree.jsx'
import { version } from 'react'
import apiCall from './backendConfig.jsx';
import { useParams } from 'react-router-dom';

function Programmer(props) {

  const { experiment, set_experiment } = useContext(ExperimentContext)

  const modify_experiment = (key, value) => {
    set_experiment(previous_value => ({ ...previous_value, [key]: value }))
  }
  const loading = useRef(true)
  if (loading.current == "done") {
    loading.current = false
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

  const [color_lib, set_color_lib] = useState(new Map())


  color_lib.entries().forEach(([key, color]) => {
    const form_ids = JSON.parse(key)
    form_ids.forEach(id => {
      const color_array = experiment.forms[id]?.colors
      if (!color_array) {
        return
      }
      if (!color_array.includes(color)) {
        color_array.push(color)
      }
    })
  })

  const modifyForms = (formObject) => {
    const tmp = structuredClone(experiment.forms)
    tmp[formObject.id] = formObject
    setForms(tmp)
  }

  const addEmptyForm = () => {
    const current_form_count = Object.keys(experiment.forms).length
    console.log(current_form_count)
    const tmp = structuredClone(experiment)
    let new_id = uuidv4()
    if (current_form_count == 0) {
      new_id = "form_0"
    } else {
      tmp.forms[experiment.selected_id].is_selected = false
    }
    const empty_form = {
      id: new_id,
      method: "constant",
      well_array: [],
      colors: [],
      is_selected: true,
      index: current_form_count
    }
    tmp.forms[new_id] = empty_form
    tmp.selected_id = new_id
    set_experiment(tmp)
  }

  if (loading.current == true) {
    loading.current = "done"
    console.log("forms: ", Object.keys(experiment.forms))
    if (Object.keys(experiment.forms).length === 0)
      addEmptyForm()
  }


  const deleteForm = (event) => {
    const target_id = event.target.id
    console.log("deleting form with id: ", target_id)
    const { [target_id]: _, ...new_forms_object } = experiment.forms;
    set_color_lib(new Map())
    setForms(new_forms_object)
  }

  const keydownHandler = (event) => {
    if (["Enter", "Escape"].includes(event.key)) {
      event.target.blur()
    }
  }

  const simulate_experiment = () => {
    const plate_output = control_call({
      route: "simulate_experiment",
      body: {
        experiment: experiment
      }
    }).then(data =>
      console.log(data))
  }

  return (
    <div id="experiment">
      <div id="forms">
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
        <div className="sheet-wrap">
          {Object.keys(experiment.forms).map((form_id) => (
            <InstructionForm
              id={form_id}
              key={form_id}
            />
          ))}
        </div>
        <button className="add-form-btn" onClick={addEmptyForm}>+ add reagent</button>
      </div>
      <div id="visualElements">
        <button onClick={simulate_experiment}>simulate experiment</button>
        <PlateElement set_color_lib={set_color_lib} />
        <ComboTree color_lib={color_lib} />
      </div>
    </div>
  )
}
export default Programmer
