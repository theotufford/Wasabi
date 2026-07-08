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
          <button onClick={props.send_buzz}>buzz motor</button>
          <button commandfor={id} type="submit" command="close" >confirm and commit physical change</button>
        </div>
      </form>
    </dialog>
  )

  if (experiment_reagents.includes(reagent)) {
    return (
      <>
        {id} has {reagent}, no change needed
        {change_modal}
      </>
    )
  }

  return (
    <>
      {id} has '{reagent}', not used in loaded experiment <button command="show-modal" commandfor={id}>change</button>
      {change_modal}
    </>
  )
}

export default Pump_block
