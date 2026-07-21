import { useState, useRef, useEffect, createContext } from 'react'
import Programmer from './Programmer.jsx'
import { apiCall, get_url_param, set_url_param, get_url_experiment } from './backendConfig.jsx'
import { ExperimentContext } from './experiment_context.jsx'
import BrowserElement from './browserFrame.jsx'
import Controller from './controller.jsx'
import Auth from './auth.jsx'
import { useReducer } from 'react'

const empty_experiment = {
  title: "",
  version: 0,
  plateDimensions: { rows: 8, columns: 12 },
  forms: {}
}

function App() {
  const [experiment, set_experiment] = useState(empty_experiment)

  const update_experiment = async () => {
    get_url_experiment().then(found_experiment => {
      console.log(found_experiment)
        if (found_experiment == false || found_experiment == undefined) {
          return
        }
        console.log("setting experiment to", found_experiment)
        set_experiment(found_experiment)
      })
  }

  const url_title = get_url_param("title")
  if (experiment.title != url_title) {
    update_experiment()
  }

  useEffect(() => {
    update_experiment()
  }, [])

  const window_state = useRef("controller")
  const [author, set_author] = useState("anon")

  const goToController = () => {
    window_state.current = "controller"
    set_selected_window(<Controller />)
  }

  const goToEditor = () => {
    window_state.current = "editor"
    set_selected_window(
      <Programmer/>)
  }


  const [selected_window, set_selected_window] = useState(
    <Controller/>
  )

  const new_experiment = () => {
    set_url_param("title", "")
    set_url_param("version", 0)
    set_experiment(empty_experiment)
    goToEditor()
  }

  let button_to_show

  console.log("experiment is", experiment)
  if (window_state.current === "controller") {
    button_to_show = <button onClick={goToEditor}>edit {experiment.title}</button>
  } else {
    button_to_show = <button onClick={goToController} > control interface</button>
  }

  return (
    <ExperimentContext value={{
      experiment,
      set_experiment
    }}>
      <div className='nav_bar'>
        {button_to_show}
        <button onClick={new_experiment}>create new experiment</button>
      </div >
      {selected_window}
      <button command="show-modal" commandfor="browser">pick experiment</button>
      <BrowserElement
        author={author}
        experiment={experiment}
        set_experiment={set_experiment}
      />
    </ExperimentContext>
  )
}
export default App
