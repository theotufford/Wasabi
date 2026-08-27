import { useState, useRef, useEffect, createContext } from 'react'
import { BrowserRouter, Routes, Route, Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { ExperimentContextProvider } from './ExperimentContextProvider.jsx';
import "./App.css"
import Controller from './Controller/controller.jsx'
import Programmer from './Programmer/Programmer.jsx'
import { useContext } from 'react';
import { empty_experiment, ExperimentContext } from './ExperimentContext.jsx';

function App() {
  const { experiment, set_experiment } = useContext(ExperimentContext)
  const location = useLocation()
  const navigate = useNavigate('/programmer')
  const make_new_experiment = () => {
    set_experiment(empty_experiment)
    navigate("/programmer")
  }
  return (
    <div>
      <div className='nav-bar'>
        <nav> {
          location.pathname == "/programmer" ?
            <NavLink className="nav-link" to="/controller">controller</NavLink>
            : <Link className="nav-link" to="/programmer">
              {
                experiment === empty_experiment ? <>programmer</> : <>edit {experiment.title}</>
              }
            </Link>
        }
        </nav>
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
