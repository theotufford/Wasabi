import { useState, useRef, useEffect } from 'react'
import Programmer from './Programmer.jsx'
import BrowserElement from './browserFrame.jsx'
import Controller from './controller.jsx'

function App() {
  const empty_experiment_initial = {
    title: "",
    version: 0,
    plateDimensions: { rows: 8, columns: 12 },
    forms: {}
  }

  const experiment = useRef(empty_experiment_initial)
  const window_state = useRef("controller")

  const goToController = () => {
    window_state.current = "controller"
    set_selected_window(
      <Controller
        experiment={experiment}
      />
    )
  }

  const goToEditor = () => {
    window_state.current = "editor"
    set_selected_window(
      <Programmer
        experiment={experiment}
        goToController={goToController}
      />)
  }

  const open_browser = () => {
    window_state.current = "browser"
    set_selected_window(
      <BrowserElement
        experiment={experiment}
        goToEditor={goToEditor}
        goToController={goToController}
      />
    )
  }

  const [selected_window, set_selected_window] = useState(
    <Controller
      experiment={experiment}
    />
  )

  const new_experiment = () => {
    experiment.current = empty_experiment_initial
    open_browser()
    goToEditor()
  }



  const in_controller = window_state.current === "controller"
  const in_browser = window_state.current === "browser"

  const enable_edit_button = in_controller && experiment.current.title != ""

  return (
    <>
      <div>
        <button
          style={{ visibility: !in_browser ? 'visible' : 'hidden' }}
          onClick={open_browser}>browse experiments</button>
        <button
          style={{ visibility: enable_edit_button ? 'visible' : 'hidden' }}
          onClick={goToEditor}>edit {experiment.current.title}</button>
        <button
          onClick={new_experiment}>create new experiment</button>
        <button
          style={{ visibility: !in_controller ? 'visible' : 'hidden' }}
          onClick={goToController}>control interface</button>
      </div>
      {selected_window}
    </>
  )
}
export default App
