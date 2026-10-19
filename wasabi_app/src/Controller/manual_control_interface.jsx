import { useState, useRef, useEffect, useContext } from 'react'
import { apiCall, control_call, dataStream } from '@src/backendConfig.jsx'
import Pump_row from './pump_row.jsx'
import TestButton from '@src/browserFrame.jsx'
import { Reagent_Selector } from '../Reagent_Selector.jsx'
import "./controller.css"
import { AppGlobalContext } from '@src/AppGlobalContext.jsx'

function Jogger(props) {

  const send_home = () => {
    control_call({ route: "home" })
  }

  const send_set_waste_position = () => {
    control_call({ route: "set_waste_position" })
  }

  const xy_jogIncrement = useRef(0)
  const z_jogIncrement = useRef(0)

  const jog = (delta_x, delta_y, delta_z) => {
    control_call({
      route: "move",
      body: {
        move_context: "jog",
        delta: [delta_x, delta_y, delta_z]
      }
    })
  }


  const goto_well = (wellid) => {
    control_call({
      route: "move",
      body: {
        move_context: "well",
        well_target: wellid
      }
    })
  }
  return (
    <div className='jogger'>

      <div className='xy_jog'>
        <label for="xyjog">X/Y jog increment: </label>
        <input name='xyjog' type="number" onChange={(e) => {
          const val = e.target.valueAsNumber
          if (isNaN(val)) { return }
          xy_jogIncrement.current = val
        }} />

        <div className='xy_control_buttons'>
          <button onClick={() => jog(xy_jogIncrement.current, 0, 0)} >+x</button>
          <button onClick={() => jog(-xy_jogIncrement.current, 0, 0)} >-x</button>
          <button onClick={() => jog(0, xy_jogIncrement.current, 0)} >+y</button>
          <button onClick={() => jog(0, -xy_jogIncrement.current, 0)} >-y</button>
        </div>
      </div>

      <div className='z_jog'>
        <label for="zjog">z jog increment: </label>
        <input name='zjog' type="number" onChange={(e) => {
          const val = e.target.valueAsNumber
          if (isNaN(val)) { return }
          z_jogIncrement.current = val
        }} />
        <button onClick={() => jog(0, 0, -z_jogIncrement.current)} >-z</button>
        <button onClick={() => jog(0, 0, z_jogIncrement.current)} >+z</button>
      </div>
      <button onClick={send_home}>home</button>
      <button onClick={() => control_call({route: "set_top_left"})} > set top left </button>
      <button onClick={() => control_call({route: "set_bottom_right"})} > set bottom right </button>
      <button onClick={() => goto_well("A1")}>goto A1</button>
      <button onClick={() => goto_well("A12")}>goto A12</button>
      <button onClick={() => goto_well("H1")}>goto H1</button>
      <button onClick={() => goto_well("H12")}>goto H12</button>
      <button onClick={send_set_waste_position}>set waste position</button>
    </div>
  )
}
export default Jogger 
