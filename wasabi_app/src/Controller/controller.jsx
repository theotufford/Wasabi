import { useState, useRef, useEffect, useContext } from 'react'
import { apiCall, control_call, dataStream } from '@src/backendConfig.jsx'
import Pump_block from './pump_interface.jsx'
import TestButton from '@src/browserFrame.jsx'
import { Reagent_Selector } from '../Reagent_Selector.jsx'
import "./controller.css"
import { AppGlobalContext } from '@src/AppGlobalContext.jsx'

function Controller(props) {
  const { experiment, set_experiment } = useContext(AppGlobalContext)
  const [serialMessage, setSerialMessage] = useState(".....")
  const [pump_array, set_pump_array] = useState({})
  const [reagents, set_reagents] = useState([])
  const [reagents_needed, set_reagents_needed] = useState([])


  const load_needed = () => {
    console.log("pump array: ", pump_array)
    const tmp = []
    Object.keys(experiment.forms).forEach((form_id) => {
      const form = experiment.forms[form_id]
      const reagent = form.reagent
      if (tmp.includes(reagent)) {
        return
      }
      tmp.push(reagent)
    })
    set_reagents(tmp)
    set_reagents_needed(tmp.filter(reagent => (!Object.values(pump_array).includes(reagent))))
  }


  // on page load
  useEffect(() => {
    dataStream.onmessage = (e) => {
      console.log("received: ", e)
      setSerialMessage(e.data)
    }
    //get and set key value pump array from backend db
    apiCall({ route: "get_pump_map" })
      .then(apiResponse => apiResponse.data)
      .then(data => {
        set_pump_array(data)
      })
  }, [])

  useEffect(() => {
    load_needed()
  }, [pump_array, experiment])


  let title_text = "no experiment loaded"
  if (experiment.title != "") title_text = experiment.title;

  const send_home = () => {
    control_call({ route: "home" })
  }
  const send_set_home_offset = () => {
    control_call({ route: "set_home_offset" })
  }
  const send_set_waste_position = () => {
    control_call({ route: "set_waste_position" })
  }

  const send_run_experiment = () => {
    control_call({
      route: "run_experiment",
      body: {
        experiment: experiment
      }
    })
  }

  // x/y and z respectively
  const jogIncrement = useRef([0, 0])
  const move_target = useRef([0, 0, 0])

  const jog = (delta_x, delta_y, delta_z) => {
    control_call({
      route: "move",
      body: {
        move_context: "jog",
        delta: [delta_x, delta_y, delta_z]
      }
    })
  }


  const go_to_well = (wellid) => {
    control_call({
      route: "move",
      body: {
        move_context: "well",
        well_target: wellid
      }
    })
  }

  const go_to_pos = (move_type) => {
    control_call({
      route: "move",
      body: {
        move_context: move_type,
        target: move_target
      }
    })
  }

  return (
    <div className='controller'>
      <div>
        current experiment: {title_text}
      </div>
      <div className='jogger'>
        <div className='xy_jog'>
          <label for="xyjog">X/Y jog increment: </label>
          <input name='xyjog' type="number" onChange={(e) => {
            const val = e.target.valueAsNumber
            if (isNaN(val)) { return }
            jogIncrement.current = ([val, jogIncrement.current[1]])
          }} />
          <div className='xy_control_buttons'>
            <button onClick={() => jog(jogIncrement.current[0], 0, 0)} >+x</button>
            <button onClick={() => jog(-jogIncrement.current[0], 0, 0)} >-x</button>
            <button onClick={() => jog(0, jogIncrement.current[0], 0)} >+y</button>
            <button onClick={() => jog(0, -jogIncrement.current[0], 0)} >-y</button>
          </div>
        </div>
        <div className='z_jog'>
          <label for="zjog">z jog increment: </label>
          <input name='zjog' type="number" onChange={(e) => {
            const val = e.target.valueAsNumber
            if (isNaN(val)) { return }
            jogIncrement.current = ([jogIncrement.current[0], val])
          }} />
          <button onClick={() => jog(0, 0, jogIncrement.current[1])} >+z</button>
          <button onClick={() => jog(0, 0, -jogIncrement.current[1])} >-z</button>
        </div>
        <button onClick={send_home}>home</button>
        <button onClick={send_set_home_offset}>set A1</button>
        <button onClick={() => go_to_well("A1")}>go A1</button>
        <button onClick={send_set_waste_position}>set waste position</button>
        <button onClick={() => go_to_well("waste")}>go to waste well</button>
      </div>
      <div className='pump_bay'>
        {reagents_needed.length > 0 && (
          <ul>
            {reagents_needed.map(name => (<li>{name}</li>))}
          </ul>)}
        {
          Object.keys(pump_array).map((id) => (
            <div>
              <Pump_block
                key={id} id={id}
                reagent={pump_array[id]}
                reagents={reagents}
                set_pump_array={set_pump_array}
                reagents_needed={reagents_needed}
                load_needed={load_needed} />
            </div>
          ))
        }
      </div>
      <button onClick={send_run_experiment}>run experiment!!</button>
    </div>
  )
}
export default Controller
