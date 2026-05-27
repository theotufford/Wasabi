import { useState, useRef, useEffect } from 'react'
import { apiCall, dataStream } from './backendConfig.jsx'
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
  const [pump_array, set_pump_array] = useState(Object.entries({}))
  useEffect(() => {
    console.log(dataStream)
    dataStream.onmessage = (e) => {
      setSerialMessage(e.data)
    }
    //get and set key value pump array from backend db
    apiCall({ route: "get_pump_map" })
      .then(apiResponse => apiResponse.data)
      .then(data => {
        set_pump_array(Object.entries(data))
        console.log(Object.entries(data))
      })
  }, [])

  let title_text = "no experiment loaded"
  if (experiment.title != "") title_text = experiment.title;

  return (
    <div>
      <div>
        current experiment: {title_text}
      </div>
      <div>Serial says:
        <div className='serial_display'>{serialMessage}</div>
      </div>
    pumps:
      {pump_array.map(([pump_id, reagent]) => (
        <div>
          {pump_id} has: {reagent} <button> buzz motor </button>
        </div>
      ))}
    </div>
  )
}
export default Controller
