import { createContext } from "react"
import methods from '@src/assets/methods.json'
import machine_data from '@src/assets/machine_config.json'



const default_method = "volume_map"
const default_fixture = "std_plate_fixture"
const default_plate = "standard 96"

export const get_method_input_default = (input) => {
  const empty_value = {
    _empty: "",
    dict: {},
    Plate_Map: {},
    Named_Container: {
      name: "",
      contents: {},
      is_reservoir: false
    },
    float: 0,
    int: 0,
    Volume: 0,
    Reagent: "",
    Wellid: "",
    Literal: input.args?.[0],
    list: []
  }
  return empty_value[input.type]
}

const get_new_method_input_record = (method_name) => {
  const inputs = methods[method_name]
  const input_record = {}
  Object.entries(inputs).forEach(([argname, meta]) => {
    input_record[argname] = get_method_input_default(meta)
  })
  console.log("input record: ", input_record)
  return input_record
}

export const default_form = {
  id: "form_0",
  method: default_method,
  is_selected: true,
  index: 0,
  method_meta: methods[default_method],
  ...get_new_method_input_record(default_method)
}


export const empty_experiment = {
  id: 0,
  author: "anonymous",
  title: "",
  version: 0,
  plate: machine_data.plates[default_plate],
  fixture: machine_data.fixtures[default_fixture],
  forms: { [default_form.id]: default_form },
  selected_id: default_form.id,
  simulated_platemap: {}
}



export const AppGlobalContext = createContext(null)

