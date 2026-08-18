import { useContext } from "react"
import { ExperimentContext } from "./ExperimentContext"
import apiCall from "./backendConfig"
import { useState } from "react"
import { useEffect } from "react"
import { useParams, useSearchParams } from "react-router-dom"

const empty_experiment = {
  title: "",
  version: 0,
  plateDimensions: { rows: 8, columns: 12 },
  forms: {
    form_0: {
      id: "form_0",
      method: "constant",
      well_array: [],
      is_selected: true,
      index: 0,
      colors: []
    }
  },
  selected_id: "form_0",
  simulated_platemap: {}
}

export const ExperimentContextProvider = ({ children }) => {
  const [params, set_params] = useState({
    title: "", // default value only used if other value not given
    version: 0,
  })

  // calls fetch experiment on first load to get experiment by title/version in the search params
  const [experiment, set_experiment] = useState(empty_experiment)

  const load_experiment = async (title, version) => {
    // if search params are default it sets the experiment to be empty
    if (params.title == "") {
      set_experiment(empty_experiment)
      return
    }
    await apiCall({
      route: "fetchExperiment",
      body: { title: title, version: version }
    })
      .then(fetched_experiment => {
        if (fetched_experiment?.failure == true) {
          set_experiment(empty_experiment)
        }
        else {
          // if it gets back an experiment record from the api it will set it
          return set_experiment(fetched_experiment)
        }
      })
  }

  useEffect(() => { load_experiment() }, [])


  useEffect(() => {
    if (params.title == experiment.title && params.version == experiment.version) {
      return
    }
    set_params({ title: experiment.title, version: experiment.version })
  }, [experiment])


  // explicit load alternative experiment function
  // db is only the experiment provider when absolutely necessary
  // otherwise it just catches autosaves
  return (
    <ExperimentContext value={{
      experiment: experiment,
      set_experiment: set_experiment,
      load_experiment: load_experiment
    }}>
      {children}
    </ExperimentContext>
  )

}
