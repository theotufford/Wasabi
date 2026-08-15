import { useState, useRef, useEffect, useContext } from 'react'
import { apiCall, control_call, dataStream } from './backendConfig.jsx'
import Pump_block from './pump_interface.jsx'
import TestButton from './browserFrame.jsx'
import { ExperimentContext } from './ExperimentContext.jsx'

function Controller(props) {
  const { experiment, set_experiment } = useContext(ExperimentContext)
  const [serialMessage, setSerialMessage] = useState(".....")
  const [pump_array, set_pump_array] = useState({})
  const [reagents, set_reagents] = useState([])
  const [reagents_needed, set_reagents_needed] = useState([])


  useEffect(() => {
    load_needed()
  }, [experiment])

  const load_needed = () => {
    const tmp = []
    console.log("controller exp: ", experiment)
    Object.keys(experiment.forms).forEach((form_id) => {
      const form = experiment.forms[form_id]
      const reagent = form.reagent
      console.log("REAGENT", reagent)
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
    load_needed()
  }, [])

  let title_text = "no experiment loaded"
  if (experiment.title != "") title_text = experiment.title;

  const send_home = () => {
    control_call({ route: "home" })
  }

  const send_set_home_offset = () => {
    control_call({ route: "set_home_offset" })
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
    <div>
      <div>
        current experiment: {title_text}
      </div>
      <div>Serial says:
        <div className='serial_display'>{serialMessage}</div>
      </div>
      <div>
        <div>
          <input type="number" onChange={(e) => {
            const val = e.target.valueAsNumber
            if (isNaN(val)) { return }
            jogIncrement.current = ([val, jogIncrement.current[1]])
          }} />
          <button onClick={() => jog(jogIncrement.current[0], 0, 0)} >+x</button>
          <button onClick={() => jog(-jogIncrement.current[0], 0, 0)} >-x</button>
          <button onClick={() => jog(0, jogIncrement.current[0], 0)} >+y</button>
          <button onClick={() => jog(0, -jogIncrement.current[0], 0)} >-y</button>
        </div>
        <div>
          <input type="number" onChange={(e) => {
            const val = e.target.valueAsNumber
            if (isNaN(val)) { return }
            jogIncrement.current = ([jogIncrement.current[0], val])
          }} />
          <button onClick={() => jog(0, 0, jogIncrement.current[1])} >+z</button>
          <button onClick={() => jog(0, 0, -jogIncrement.current[1])} >-z</button>
        </div>
      </div>
      <button onClick={send_home}>home and set work offset</button>
      <div>
      </div>
      <>
        reagents needed for experiment that arent loaded: <ul>
          {reagents_needed.map(name => (<li> - {name}</li>))}
        </ul>
        {
          Object.keys(pump_array).map((id) => (
            <div>
              <Pump_block
                key={id} id={id}
                reagent={pump_array[id]}
                reagents={reagents}
                set_pump_array={set_pump_array}
                reagents_needed={reagents_needed} />
            </div>
          ))
        }
      </>
      <button onClick={send_run_experiment}>run experiment!!</button>
    </div>
  )
}
export default Controller
