import { useRef } from "react"

function Pump_block(props) {
  const id = props.id
  const reagents_needed = props.reagents_needed
  const reagents = props.reagents
  const pump_array = props.pump_array

  const selected_reagent = useRef("")
  const current = pump_array[id]
  const commit = () => {
    console.log("committed")
  }
  const change_modal = (
    <dialog id={id}>
      <p>reagent associated with this motor: {current}</p>
      options:
      <select onChange={(e) => { selected_reagent.current = e.target.value }}>
        {
          reagents_needed.map((reagent) => {
            return (<option key={reagent} value={reagent}>{reagent}</option>)
          })
        }
      </select>
      <div>
        <button onClick={props.send_buzz}>buzz motor</button>
        <button onClick={commit} commandfor={id} command="close" >confirm and commit physical change</button>
      </div>
    </dialog>
  )
  console.log("pump array on rgd call: ", pump_array)
  if (reagents.current.includes(current)) {
    return (
      <>
        {id} has '{current}', no change needed,
        {change_modal}
      </>
    )
  }

  return (
    <>
      {id} has '{current}', not used in loaded experiment <button command="show-modal" commandfor={id}>change</button>
      {change_modal}
    </>
  )
}

export default Pump_block
