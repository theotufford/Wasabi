import { useContext } from "react"
import { ExperimentContext } from "./ExperimentContext"
import apiCall from "./backendConfig"
import { useState } from "react"
import { useEffect } from "react"
import { useParams, useSearchParams } from "react-router-dom"
import { empty_experiment } from "./ExperimentContext"

export const ExperimentContextProvider = ({ children }) => {
  const [experiment, set_experiment] = useState(() => {
    // const saved_exp = localStorage.getItem("experiment")
    // return saved_exp !== null ? JSON.parse(saved_exp) : empty_experiment
    return empty_experiment
  })

  useEffect(() => {
    localStorage.setItem("experiment", JSON.stringify(experiment))
  }, [experiment])

  const load_experiment = async (title, version) => {
    // if search params are default it sets the experiment to be empty
    if (title == "") {
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
