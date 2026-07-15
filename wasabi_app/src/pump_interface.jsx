import { useState } from "react"
import { useRef } from "react"
import { apiCall, control_call } from './backendConfig.jsx'


function Pump_block(props) {
  const id = props.id
  const reagents_needed = props.reagents_needed
  const experiment_reagents = props.reagents
  const [reagent, setReagent] = useState(props.reagent)

  const commit = (data) => {
    const new_reagent = data.get('reagent-select')
    setReagent(new_reagent)
    props.set_pump_array(prev => (
      { ...prev, [id]: new_reagent }
    ))
    apiCall({
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
  }

  const pump_action = (data) => {
    const volume_ul = data.get("volume")
    control_call(
      {
        route: "pump_action",
        body: {
          volume: volume_ul,
          id: id
        }
      }
    )
  }

  const change_modal = (
    <dialog id={id}>
      <form action={commit}>
        <select name="reagent-select">
          <option value={props.reagent} >{props.reagent}</option>
          {
            reagents_needed.map((needed_reagent) => {
              return (
                <option key={needed_reagent} value={needed_reagent}>
                  {needed_reagent}
                </option>
              )
            })
          }
        </select>
        <div>
          <button type="button" onClick={send_buzz}>buzz motor</button>
          <button commandfor={id} type="submit" command="close" >confirm and commit physical change</button>
        </div>
      </form>
    </dialog>
  )

  if (experiment_reagents.includes(reagent)) {
    return (
      <>
        {id} has {reagent}, no change needed <button onClick={send_buzz}>buzz motor</button>
        {change_modal}
      </>
    )
  }

  return (
    <div>
      pump {id} has '{reagent}', not used in loaded experiment <button command="show-modal" commandfor={id}>change</button>
      <button onClick={send_buzz}>buzz motor</button>
      <form action={pump_action}>
        <input name="volume" type="number" placeholder="pump volume ul" /> <button type="submit">o</button>
      </form>
      {change_modal}
    </div>
  )
}

export default Pump_block
