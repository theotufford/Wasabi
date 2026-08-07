import { createContext } from "react"

export const ExperimentContext = createContext(
  {
    title: "",
    version: 0,
    plateDimensions: { rows: 8, columns: 12 },
    forms: {
      form_0: {
        id: "form_0",
        ethod: "constant",
        well_array: [],
        is_highlighted: true,
        index: 0
      }
    }
  }
)
