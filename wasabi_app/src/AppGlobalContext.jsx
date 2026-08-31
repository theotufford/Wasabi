import { createContext } from "react"
import methods from '@src/assets/methods.json'

const default_method = "volume_map"

const get_method_input_default = (input) => {
  const empty_value = {
    _empty: "",
    dict: {},
    float: 0,
    int: 0,
    Literal: input.args?.[0],
    list: []
  }
  return empty_value[input.type]
}

const get_new_method_input_record = (method_name) => {
  const inputs = methods[method_name].inputs
  const inputname_default_pairs = inputs.map((input) => [input.name, get_method_input_default(input)])
  return Object.fromEntries(inputname_default_pairs)
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
  title: "",
  version: 0,
  plateDimensions: { rows: 8, columns: 12 },
  forms: { [default_form.id]: default_form },
  selected_id: "form_0",
  simulated_platemap: {}
}


export const AppGlobalContext = createContext(null)

