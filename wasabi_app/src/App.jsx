import { useState, useRef, useEffect, createContext } from 'react'
import { BrowserRouter, Routes, Route, Link, NavLink } from 'react-router-dom';
import Programmer from './Programmer.jsx'
import { ExperimentContextProvider } from './ExperimentContextProvider.jsx';
import Controller from './controller.jsx'
import { useContext } from 'react';

function App() {
  return (
    <BrowserRouter>
      <ExperimentContextProvider>
        <nav>
          <NavLink to="/controller">controller</NavLink>
          <NavLink to="/programmer">programmer</NavLink>
          <Link to="/programmer">make new experiment</Link>
        </nav>
        <Routes>
          <Route path='/controller' element={<Controller/>} />
          <Route path='/' element={<Controller/>} />
          <Route path='/programmer' element={<Programmer/>} />
        </Routes>
      </ExperimentContextProvider>
    </BrowserRouter>
  )
}
export default App
