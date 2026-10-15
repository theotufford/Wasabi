import { BrowserRouter, Routes, Route, Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { AppGlobalContextProvider } from './AppGlobalContextProvider.jsx';
import "./App.css"
import { v4 as uuidv4 } from 'uuid';
import Controller from './Controller/controller.jsx'
import Programmer from './Programmer/Programmer.jsx'
import { useContext, useState } from 'react';
import { empty_experiment, AppGlobalContext } from './AppGlobalContext.jsx';
import apiCall from './backendConfig.jsx';
import BrowserElement from './browserFrame.jsx';
import SaveButton from './Programmer/SaveButton.jsx';

function New_Experiment_Modal(props) {
  const { experiment, set_experiment } = useContext(AppGlobalContext)
  const exp = empty_experiment
  exp.id = uuidv4()
  const update_title = (e) => {
    exp.title = e.target.value
  }
  const update_author = (e) => {
    const newauthor = e.target.value
    if (newauthor != "") {
      exp.author = newauthor
    }
  }

  const handle_submit = () => {
    set_experiment(exp)
    apiCall({
      route: "saveExperiment",
      body: { ...experiment, autosave: false}
    })
    const dialog_target = document.getElementById("new_experiment")
    dialog_target.close()
  }

  return (
    <dialog key={props.key} id="new_experiment">
      make new experiment:
      title: <input onChange={update_title} />
      author:<input onChange={update_author} />
      <button onClick={handle_submit}>create new</button>
    </dialog>
  )
}


function App() {
  const { experiment, set_experiment } = useContext(AppGlobalContext)
  const location = useLocation()
  return (
    <div>
      <div classtitle='nav-bar'>
        <nav> {
          location.pathname == "/programmer" ?
            <NavLink classtitle="nav-link" to="/controller">controller</NavLink>
            : <Link classtitle="nav-link" to="/programmer">
              {
                experiment === empty_experiment ? <>programmer</> : <>edit {experiment.title}</>
              }
            </Link>
        }
        </nav>
        <BrowserElement/>
        <New_Experiment_Modal/>
        <button command="show-modal" commandfor="browser" classtitle="nav-bar-button">open different experiment</button>
        <button command="show-modal" commandfor="new_experiment" classtitle="nav-bar-button">new experiment</button>
      </div>
      <Routes>
        <Route path='/' element={<Controller />} />
        <Route path='/controller' element={<Controller />} />
        <Route path='/programmer' element={<Programmer />} />
      </Routes>
    </div>
  )
}
export default App
