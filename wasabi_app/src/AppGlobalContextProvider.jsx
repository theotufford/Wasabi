import { useContext } from "react"
import { AppGlobalContext } from "./AppGlobalContext"
import apiCall from "./backendConfig"
import { useState } from "react"
import { useEffect } from "react"
import { useParams, useSearchParams } from "react-router-dom"
import Keybound_Container from "./keybound_container"
import { empty_experiment } from "./AppGlobalContext"
import { useRef } from "react"

export const AppGlobalContextProvider = ({ children }) => {
  const [keybind_function_map, set_keybind_function_map] = useState(new Map())
  const keystate = useRef([])
  const [experiment, set_experiment] = useState(() => {
    const saved_exp = localStorage.getItem("experiment")
    return (
      saved_exp !== null ?
        JSON.parse(saved_exp) :
        empty_experiment
    )
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

  const update_keystate = (new_keystate) => {
    keystate.current = new_keystate
  }

  return (
    <AppGlobalContext value={{
      experiment: experiment,
      set_experiment: set_experiment,
      load_experiment: load_experiment,
      keystate: keystate,
      set_keybind_function_map: set_keybind_function_map,
    }}>
      <Keybound_Container function_map={keybind_function_map} update_keystate={update_keystate}>
        {children}
      </Keybound_Container>
    </AppGlobalContext>
  )

}
