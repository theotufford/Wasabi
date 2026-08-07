import { useState, useRef, useEffect, useContext } from 'react'
import PlateElement from './plateElement.jsx'
import InstructionForm from './InstructionForm.jsx'
import { v4 as uuidv4 } from 'uuid';
import SaveButton from './SaveButton.jsx';
import './Programmer.css'
import { get_url_param } from './backendConfig.jsx';
import { ExperimentContext } from './experiment_context.jsx';
import LegendElement from './legend.jsx'
import { version } from 'react'
import apiCall from './backendConfig.jsx';

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


  color_lib.entries().forEach(([ key, color ]) => {
    const form_ids = JSON.parse(key)
    form_ids.forEach(id => {
      const color_array = experiment.forms[id]?.colors
      if (!color_array) {
        return
      }
      if (!color_array.includes(color)){
      color_array.push(color)
      }
    })
  })

  const titleChange = (event) => {
    const title = event.target.value
    if (title === undefined) return;
    setTitle(title)
  }

  const modifyForms = (formObject) => {
    const tmp = structuredClone(experiment.forms)
    tmp[formObject.id] = formObject
    setForms(tmp)
  }

  const addEmptyForm = () => {
    const current_form_count = experiment.forms.length
    const new_id = uuidv4()
    const tmp = structuredClone(experiment.forms)
    Object.keys(experiment.forms).forEach((form_id) => {
      tmp[form_id].is_selected = false
    })
    const empty_form = {
      id: new_id,
      method: "constant",
      well_array: [],
      colors:[],
      is_selected: true,
      index: current_form_count
    }
    tmp[new_id] = empty_form
    setForms(tmp)
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

  return (
    <div id="experiment">
      <div id="forms">
        <div className="title-row">
          <input
            type="text"
            name="experimentTitle"
            defaultValue={experiment.title}
            onBlur={titleChange}
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
              className="instructionForm"
            />
          ))}
        </div>
        <button className="add-form-btn" onClick={addEmptyForm}>+ add reagent</button>
      </div>
      <div id="visualElements">
        <PlateElement set_color_lib={set_color_lib} />
        <LegendElement color_lib={color_lib} />
      </div>
    </div>
  )
}
export default Programmer
