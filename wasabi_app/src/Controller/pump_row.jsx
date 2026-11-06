import { useEffect, useState } from "react"
import { useRef } from "react"
import { apiCall, control_call, dataStream } from '@src/backendConfig.jsx'
import { Reagent_Selector } from "../Reagent_Selector"


function Pump_block(props) {
  const id = props.id
  const reagents_needed = props.reagents_needed
  const experiment_reagents = props.reagents
  const [reagent, setReagent] = useState(props.reagent)

  const commit = (new_reagent) => {
    setReagent(new_reagent)
    props.set_pump_array(prev => (
      { ...prev, [id]: new_reagent }
    ))
    control_call({
      route: "update_reagent",
      body: {
        id: id,
        reagent: new_reagent
      }
    })
  }
  const send_buzz = () => {
    control_call({
      route: "buzz",
      body: {
        id: id,
      }
    })
    props.load_needed()
  }

  const pump_action_ref = useRef(null)
  const pump_action = (event) => {
    event.preventDefault()
    control_call(
      {
        route: "pump_action",
        body: {
          volume: parseFloat(pump_action_ref.current.value),
          id: id
        }
      }
    )
  }
  const [selected_reagent, set_selected_reagent] = useState(props.reagent)
  useEffect(() => {
    commit(selected_reagent)
  }, [selected_reagent])



  return (
    <tr>
      <td>{id}</td>
      <td><button onClick={send_buzz}>buzz motor</button></td>
      <td>
        <Reagent_Selector selected_reagent={selected_reagent} select_reagent={(new_reagent) => set_selected_reagent(new_reagent)} />
      </td>
      <td>
        <input ref={pump_action_ref} name="volume" type="number" placeholder="pump volume ul" />
        <button onClick={pump_action}>o</button>
      </td>
    </tr>
  )
}

export default Pump_block
