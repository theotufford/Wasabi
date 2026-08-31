import { AppGlobalContext } from '@src/AppGlobalContext.jsx';
import './css/instructionForm.css'
import methods from '@src/assets/methods.json'
import { useContext, useEffect, useState } from 'react';


const blur_on_enter = (kd_event) => {
  if (kd_event.key == "Enter") {
    return kd_event.target.blur()
  }
}

function InstructionForm(props) {
  const { experiment, set_experiment } = useContext(AppGlobalContext)
  const this_form = experiment.forms[props.id]

  const self_destruct = () => {
    const tmp = structuredClone(experiment)
    delete tmp.forms[props.id]
    tmp.selected_id = Object.keys(tmp.forms)[0]
    console.log("updating experiment to: ", tmp)
    set_experiment(tmp)
  }

  const set_form_data = (key, value) => {
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
      set_form_data(props.name, value)
    }
    const filtered_name = props.name.replaceAll("_", " ")
    const current_value = this_form?.[props.name]
    if (props.name === "well_array") {
      return
    }
    if (props.name == "volume_map") {
      this_form.is_direct_input = true
    }
    if (props.name === "reagent") {
      return (<div> reagent: <input
        placeholder="input reagent name"
        defaultValue={current_value}
        onKeyDown={blur_on_enter}
        onBlur={mod_function} /></div>
      )
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


  const select_this_form = () => {
    if (this_form.is_selected) {
      return
    }
    const tmp = structuredClone(experiment.forms)
    tmp[experiment.selected_id].is_selected = false
    tmp[this_form.id].is_selected = true
    set_experiment((prev) => ({ ...prev, selected_id: [this_form.id], forms: tmp }))
  }
  const method_options = Object.keys(methods)
  const selected_tag = this_form.is_selected == true ? 'selected-form' : 'unselected-form'

  useEffect(() => {
    set_form_data("method_meta", methods[this_form.method])
  }, [this_form.method])


  return (
    <div className={selected_tag} onClick={select_this_form} onFocus={select_this_form}>
      <select defaultValue={this_form.method} onChange={(e) => {
        set_form_data("method", e.target.value)
      }}>
        {method_options.map((key) => {
          const filtered_name = key.replaceAll("_", " ")
          return (
            <option key={key} value={key}>{filtered_name}</option>
          )
        })}
      </select>
      <div className='method-container' key={this_form.method}>
        {this_form.method_meta.inputs.map((input) => <Method_Input {...input} />)}
      </div>
      <button onClick={self_destruct}>x</button>
    </div>
  )
}

export default InstructionForm
