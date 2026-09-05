import { useState } from "react"
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

  function Pump_reagent_swapper(props) {
    const [reagent_selected, set_reagent_selected] = useState(props.reagent)
    return (
      <dialog id={id}>
        <form action={() => commit(reagent_selected)}>
          <p>current: {props.reagent}</p>
          needed for current experiment:
          <ul>
            {
              reagents_needed.map((needed_reagent) => {
                return (<li key={needed_reagent} value={needed_reagent}>{needed_reagent}</li>)
              })
            }
          </ul>
          <Reagent_Selector select_reagent={(new_reagent) => set_reagent_selected(new_reagent)} />
          <div>
            <button commandfor={id} type="submit" command="close" >confirm and commit physical change</button>
          </div>
        </form>
      </dialog >
    )
  }

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
      <Pump_reagent_swapper />
    </div>
  )
}

export default Pump_block
