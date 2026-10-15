import { useState, useRef, useEffect, useContext } from 'react'
import { apiCall, control_call, dataStream } from '@src/backendConfig.jsx'
import Pump_row from './pump_row.jsx'
import TestButton from '@src/browserFrame.jsx'
import { Reagent_Selector } from '../Reagent_Selector.jsx'
import Jogger from './manual_control_interface.jsx'
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



  const send_run_experiment = () => {
    control_call({
      route: "run_experiment",
      body: {
        experiment: experiment
      }
    })
  }

  return (
    <div className='controller'>
      <Jogger />
      <div className='pump_bay'>
        <div className='reagents_needed_container'>
          {reagents_needed.length > 0 ?
            <div className='needed_list_container'>
              <ul>
                {reagents_needed.map(name => (<li>{name}</li>))}
              </ul>
            </div>
            : <div>
              All reagents for experiment are loaded
            </div>
          }
        </div>
        <table>
          <thead>
            <tr>
              <th>pump id</th>
              <th>buzz</th>
              <th>reagent select</th>
              <th>dispense volume</th>
            </tr>
          </thead>
          <tbody>{
            Object.keys(pump_array).map((id) => (
                <Pump_row
                  key={id} id={id}
                  reagent={pump_array[id]}
                  reagents={reagents}
                  set_pump_array={set_pump_array}
                  reagents_needed={reagents_needed}
                  load_needed={load_needed} />
            ))
          }</tbody>
        </table>
      </div>
      <button onClick={send_run_experiment}>run {experiment.title}</button>
    </div>
  )
}
export default Controller
