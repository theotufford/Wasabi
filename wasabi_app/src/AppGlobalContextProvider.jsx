import { useContext } from "react"
import { AppGlobalContext } from "./AppGlobalContext"
import apiCall from "./backendConfig"
import { useState } from "react"
import { useEffect } from "react"
import Keybound_Container from "./keybound_container"
import { empty_experiment } from "./AppGlobalContext"
import { useRef } from "react"

function check_cache_or_default(name, default_value) {
  const saved_value = localStorage.getItem(name)
  return saved_value !== null ? JSON.parse(saved_value) : default_value
}

export const AppGlobalContextProvider = ({ children }) => {
  const [keybind_function_map, set_keybind_function_map] = useState(new Map())
  const keystate = useRef([])

  const [experiment, set_experiment] = useState(check_cache_or_default("experiment", empty_experiment))
  const [serial_message, set_serial_message] = useState("")
  const [machine_state, set_machine_state] = useState({})

  useEffect(() => {
    localStorage.setItem("experiment", JSON.stringify(experiment))
  }, [experiment])

  const load_experiment = async (id, version) => {
    await apiCall({
      route: "fetchExperiment",
      body: { id: id, version: version }
    })
      .then(fetched_experiment => {
        if (fetched_experiment?.failure == true) {
          set_experiment(empty_experiment)
          alert(`couldnt find experiment with id ${id} and version ${version}`)
        }
        else {
          // if it gets back an experiment record from the api it will set it
          return set_experiment(fetched_experiment)
        }
      })
  }


  useEffect(() => {
    const streams = []
    const configure_datastream = (endpoint, message_handler) => {
      const data_stream = new EventSource(`api/${endpoint}`)
      data_stream.onmessage = (event) => {
        console.log("rx event: ", event)
        const data = JSON.parse(event.data);
        message_handler(data.message);
      };
      data_stream.onerror = (err) => {
        console.error('serial stream connection error:', err);
      };
      streams.push(data_stream)
    }

    configure_datastream("control/serial_stream", set_serial_message)
    configure_datastream("control/machine_state_stream", set_machine_state)

    return () => {
      streams.forEach(stream => { stream.close() })
    }
  }, [])

  const update_keystate = (new_keystate) => {
    keystate.current = new_keystate
  }
  const mouse_state = useRef(0)
  const mousedown_handler = (event) => {
    mouse_state.current = 1
    console.log("down")
  }
  const mouseup_handler = (event) => {
    mouse_state.current = 0
    console.log("up")
  }

  useEffect(() => {

    window.addEventListener('mousedown', mousedown_handler);
    window.addEventListener('mouseup', mouseup_handler);

    return () => {
      window.removeEventListener('mousedown', mousedown_handler);
      window.removeEventListener('mouseup', mouseup_handler);
    };
  }, [])




  return (
    <AppGlobalContext value={{
      experiment: experiment,
      set_experiment: set_experiment,
      load_experiment: load_experiment,
      keystate: keystate,
      set_keybind_function_map: set_keybind_function_map,
      mouse_state: mouse_state
    }}>
      <Keybound_Container function_map={keybind_function_map} update_keystate={update_keystate}>
        {children}
      </Keybound_Container>
    </AppGlobalContext>
  )

}
