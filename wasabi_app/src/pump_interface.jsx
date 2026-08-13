import { useState } from "react"
import { useRef } from "react"
import { apiCall, control_call, dataStream } from './backendConfig.jsx'


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
  }

  const pump_action = (event) => {
    event.preventDefault()
    const volume_ul = (new FormData(event.target)).get("volume")
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

  let content

  if (experiment_reagents.includes(reagent)) {
    content = (<> {id} has {reagent}, no change needed </>)
  } else {
    content = (<> pump {id} has '{reagent}', not used in loaded experiment </>)
  }

  return (
    <div>
      {content}
      <button command="show-modal" commandfor={id}>change</button>
      <button onClick={send_buzz}>buzz motor</button>
      <form onSubmit={pump_action}>
        <input name="volume" type="number" placeholder="pump volume ul" /> <button type="submit">o</button>
      </form>
      {change_modal}
    </div>
  )
}

export default Pump_block
