import { ExperimentContext } from './experiment_context';
import './instructionForm.css'
import methods from './assets/methods.json'
import { useContext, useState } from 'react';


const blur_on_enter = (kd_event) => {
  if (kd_event.key == "Enter") {
    return kd_event.target.blur()
  }
}

function InstructionForm(props) {
  const { experiment, set_experiment } = useContext(ExperimentContext)
  const this_form = experiment.forms[props.id]
  const self_destruct = () => {
    const tmp = structuredClone(experiment)
    delete tmp.forms[props.id]
    console.log("updating experiment to: ", tmp)
    set_experiment(tmp)
  }
  const mutate_form_data = (key, value) => {
    console.log("mutating form data with key: ", key, "value: ", value)
    const tmp = structuredClone(experiment.forms)
    tmp[props.id] = { ...this_form, [key]: value }
    set_experiment(previous_value => ({ ...previous_value, forms: tmp }))
  }
  function Method_Input(props) {
    const mod_function = (event) => {
      let value = event.target.value
      if (props.type == "float") {
        value = parseFloat(value)
      }
      if (props.type == "int") {
        value = parseInt(value)
      }
      mutate_form_data(props.name, value)
    }
    const filtered_name = props.name.replaceAll("_", " ")
    const current_value = this_form?.[props.name]
    if (props.name === "well_array") {
      return
    }
    if (props.name === "reagent") {
      return
    }
    if (props.type == "Literal") {
      return (
        <div className={props.name}>
          pick {props.name}:
          <select defaultValue={current_value} onBlur={mod_function}>
            {props.args.map((option_name) => {
              const filtered_opt_name = option_name.replaceAll("_", " ")
              return (
                <option value={option_name}>{filtered_opt_name}</option>
              )
            })}
          </select>
        </div>
      )
    }
    if (props.type == "int" || props.type == "float") {
      return (
        <input type="number"
          placeholder={filtered_name}
          defaultValue={current_value}
          onKeyDown={blur_on_enter}
          onBlur={mod_function} />
      )
    }
    if (props.type == "str") {
      return (<input
        placeholder={filtered_name}
        defaultValue={current_value}
        onKeyDown={blur_on_enter}
        onBlur={mod_function} />
      )
    }
  }

  const method_options = Object.keys(methods)
  const selected_method_info = methods[this_form.method]
  if (this_form.is_highlighted == true) {
    return (
      <div>
        <select onChange={(e) => mutate_form_data("method", e.target.value)}>
          {method_options.map((key) => {
            const filtered_name = key.replaceAll("_", " ")
            return (
              <option key={key} value={key}>{filtered_name}</option>
            )
          })}
        </select>
        {selected_method_info.inputs.map((input) => <Method_Input {...input} />)}
        <button onClick={self_destruct}>x</button>
      </div>
    )
  }
}

export default InstructionForm
