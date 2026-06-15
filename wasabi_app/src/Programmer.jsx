import { useState, useRef, useEffect } from 'react'
import PlateElement from './plateElement.jsx'
import InstructionForm from './InstructionForm.jsx'
import './Programmer.css'
import LegendElement from './legend.jsx'
import SaveButton from './flaskApi'
import { version } from 'react'

function Programmer(props) {
  const [experiment, set_experiment_ue] = useState(props.experiment.current)


  // locally we want to interface with the experiment while also updating its external context
  // but we do not want to be dealing with an external reference directly other than
  // keeping it in sync with the local one
  const setExperiment = (value) => {
    const ret = set_experiment_ue(value)
    props.experiment.current = experiment
    console.log("set current experiment to be: ", experiment)
    return ret
  }

  const setTitle = (value) => {
    setExperiment(prev => ({ ...prev, title: value }))
  }
  const setPlateDimensions = (value) => {
    setExperiment(prev => ({ ...prev, plateDimensions: value }))
  }
  const setForms = (value) => {
    setExperiment(prev => ({ ...prev, forms: value }))
  }

  const [color_lib, set_color_lib] = useState(new Map())

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
    modifyForms({
      id: crypto.randomUUID(),
      reagent: "",
      method: "constant",
      methodObject: {},
      from: "", to: "",
      colors: []
    })
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

  const loading = useRef(true)

  if (loading.current == "done") {
    loading.current = false
    setExperiment(props.experiment.current)
  }
  if (loading.current == true) {
    loading.current = "done"
  }

  useEffect(() => {
    console.log("forms: ", Object.keys(experiment.forms))
    if (Object.keys(experiment.forms).length === 0)
      addEmptyForm()
  }, [loading])

  return (
    <div id="experiment">
      <div id="forms">
        <div className="title-row">
          <input
            type="text"
            name="experimentTitle"
            defaultValue={props.experiment.current.title}
            onBlur={titleChange}
            onKeyDown={keydownHandler}
            placeholder="experiment title"
          />
          <span className="version-label">v{experiment.version}</span>
        </div>
        <div className="form-actions">
          <SaveButton experiment={experiment} setExperiment={setExperiment} />
        </div>
        <div className="sheet-wrap">
          <table>
            <thead>
              <tr>
                <th className="row-num-header"></th>
                <th>reagent</th>
                <th>method</th>
                <th>params</th>
                <th>range</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(experiment.forms).map((form_id, index) => (
                <InstructionForm
                  key={form_id}
                  className="instructionForm"
                  constructor={experiment.forms[form_id]}
                  id={form_id}
                  rowIndex={index + 1}
                  modifyForms={modifyForms}
                  deleteForm={deleteForm}
                  keydownHandler={keydownHandler}
                />
              ))}
            </tbody>
          </table>
        </div>
        <button className="add-form-btn" onClick={addEmptyForm}>+ add reagent</button>
      </div>
      <div id="visualElements">
        <PlateElement experiment={experiment} set_color_lib={set_color_lib} />
        <LegendElement experiment={experiment} color_lib={color_lib} />
      </div>
    </div>
  )
}
export default Programmer
