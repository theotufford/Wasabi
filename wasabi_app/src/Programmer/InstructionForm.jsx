import { AppGlobalContext, default_form } from '@src/AppGlobalContext.jsx';
import './css/instructionForm.css'
import methods from '@src/assets/methods.json'
import { useContext, useEffect, useState } from 'react';
import { Container_selector } from '../named_container_selector';
import { Reagent_Selector } from '../Reagent_Selector';


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
    if (length(tmp.forms) > 1) {
      delete tmp.forms[props.id]
    }
    else {
      tmp.forms[props.id] = default_form
    }
    tmp.selected_id = Object.keys(tmp.forms)[0]
    set_experiment(tmp)
  }

  const set_form_data = (key, value) => {
    const tmp = structuredClone(experiment.forms)
    tmp[props.id] = { ...this_form, [key]: value }
    set_experiment(previous_value => ({ ...previous_value, forms: tmp }))
  }


  function Method_Input({ name, type, sub_args }) {

    const mod_function = (event) => {
      let value = event.target.value
      if (type == "float" || type == "Volume") {
        value = parseFloat(value)
      }
      if (type == "int") {
        value = parseInt(value)
      }
      set_form_data(name, value)
    }

    const filtered_name = name.replaceAll("_", " ")
    const current_value = this_form?.[name]
    if (props.name === "well_array") {
      return
    }

    if (type == "Named_Container") {
      return <div>
        {filtered_name}:
        <Container_selector
          selected_container={current_value}
          select_container={(event) => set_form_data(name, event)}
        />
      </div>
    }

    if (type == "Reagent") {
      console.log("classname of ", name, "is ", type)
      return (<div> {filtered_name}: <Reagent_Selector selected_reagent={current_value} select_reagent={(event) => set_form_data(name, event)} />
      </div>
      )
    }
    if (type == "Literal") {
      return (
        <div className={name}>
          pick {name}:
          <select defaultValue={current_value} onBlur={mod_function}>
            {sub_args.map((option_name) => {
              const filtered_opt_name = option_name?.replaceAll("_", " ")
              return (
                <option value={option_name}>{filtered_opt_name}</option>
              )
            })}
          </select>
        </div>
      )
    }
    if (type == "int" || type == "float" || type == "Volume") {
      return (
        <input type="number"
          placeholder={filtered_name}
          defaultValue={current_value}
          onKeyDown={blur_on_enter}
          onBlur={mod_function} />
      )
    }
    if (type == "str") {
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
    console.log("exp ", experiment)
    console.log("this id", this_form)
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
        {Object.values(this_form.method_meta).map((input_meta) => <Method_Input {...input_meta} />)}
      </div>
      <button onClick={self_destruct}>x</button>
    </div>
  )
}

export default InstructionForm
