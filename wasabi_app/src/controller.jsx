import { useState, useRef, useEffect } from 'react'
import { apiCall, control_call, dataStream } from './backendConfig.jsx'
import Pump_block from './pump_interface.jsx'
import TestButton from './browserFrame.jsx'

function Controller(props) {
  const experiment = props.experiment.current
  // TODO:
  // live position
  // home button
  // run button
  // reagent table
  // data stream

  const [serialMessage, setSerialMessage] = useState(".....")
  const [pump_array, set_pump_array] = useState({})

  const reagents = useRef([])

  const get_reagents_needed = () => {
    const needed = reagents.current.filter(reagent => (!Object.values(pump_array).includes(reagent)))
    console.log("needed: ", needed)
    return needed
  }

  // on page load
  useEffect(() => {
    dataStream.onmessage = (e) => {
      setSerialMessage(e.data)
    }
    //get and set key value pump array from backend db
    apiCall({ route: "get_pump_map" })
      .then(apiResponse => apiResponse.data)
      .then(data => {
        set_pump_array(data)
      })
    Object.keys(experiment.forms).forEach((form_id) => {
      const form = experiment.forms[form_id]
      if (reagents.current.includes(form.reagent)) {
        return
      }
      reagents.current.push(form.reagent)
    })
    get_reagents_needed()
  }, [])

  let title_text = "no experiment loaded"
  if (experiment.title != "") title_text = experiment.title;

  const send_buzz = (id) => {
    control_call({
      route: "fetchExperiment",
      body: {
        id: id,
      }
    })
  }

  const send_home = () => {
    control_call({ route: "home" })
  }

  const jogIncrement = useRef([0, 0])

  const jog = (delta_x, delta_y, delta_z) => {
    control_call({
      route: "jog",
      body: {
        delta: [delta_x, delta_y, delta_z]
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
            jogIncrement.current = ([val, jogIncrement[1]])
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
            jogIncrement.current = ([jogIncrement[0], val])
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
          {get_reagents_needed().map(name => (<li> - {name}</li>))}
        </ul>
        {
          Object.keys(pump_array).map((id) => (
            <div>
              <Pump_block
                key={id} id={id}
                send_buzz={() => send_buzz(id)}
                reagent={pump_array[id]}
                reagents={reagents.current}
                set_pump_array={set_pump_array}
                reagents_needed={get_reagents_needed()} />
            </div>
          ))
        }
      </>
    </div>
  )
}
export default Controller
