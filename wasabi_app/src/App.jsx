import { useState, useRef, useEffect } from 'react'
import { useLocation, useParams, useSearchParams } from 'react-router-dom'
import Programmer from './Programmer.jsx'
import { apiCall, set_url_param, get_url_param } from './backendConfig.jsx'
import BrowserElement from './browserFrame.jsx'
import Controller from './controller.jsx'
import Auth from './auth.jsx'

function App() {
  const empty_experiment_initial = {
    title: "",
    version: 0,
    plateDimensions: { rows: 8, columns: 12 },
    forms: {}
  }


  const experiment = useRef(empty_experiment_initial)
  const title = get_url_param("title")
  console.log("title: ", title)


  const load_url_experiment = () => {
    apiCall({
      route: "fetchExperiment",
      body: {
        title: title,
      }
    })
      .then(response => JSON.parse(response.data))
      .then(data => { experiment.current = data })
  }


  if (title != experiment.current.title) {
    load_url_experiment()
  }

  const window_state = useRef("controller")
  const [author, set_author] = useState("anon")

  useEffect(() => {
    load_url_experiment()
  }, [window_state])


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
        author={author}
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

  let button_to_show

  if (window_state.current === "controller") {
    button_to_show = <button onClick={goToEditor}>edit {experiment.current.title}</button>
  } else {
    button_to_show = <button onClick={goToController} > control interface</button>
  }


  return (
    <>
      <div className='info bar'> <Auth author={author} set_author={set_author} /> current author: {author} </div>
      <div className='nav_bar'>
        {button_to_show}
        <button onClick={new_experiment}>create new experiment</button>
      </div >
      {selected_window}
    </>
  )
}
export default App
