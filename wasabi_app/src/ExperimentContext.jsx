import { createContext } from "react"
import methods from '@src/assets/methods.json'

const default_method = "volume_map"

export const default_form = {
  id: "form_0",
  method: default_method,
  well_array: [],
  is_selected: true,
  index: 0,
  method_meta: methods[default_method]
}

export const empty_experiment = {
  title: "",
  version: 0,
  plateDimensions: { rows: 8, columns: 12 },
  forms: { [default_form.id]: default_form },
  selected_id: "form_0",
  simulated_platemap: {}
}


export const ExperimentContext = createContext(null)

