import { useContext, useRef, useEffect, useState } from "react"
import apiCall from "../../backendConfig"
import { get_int_array } from "../utils"
import { alph } from "../utils"
import { make_plate_matrix } from "../utils"
import { AppGlobalContext } from "../../AppGlobalContext"


function outcome_well_object(props) {

}

function PureOutcomePlate(props) {
  const { keystate, set_keybind_function_map, experiment, set_experiment } = useContext(AppGlobalContext)
  const rows = experiment.plateDimensions.rows
  const columns = experiment.plateDimensions.columns
  const selected_form = experiment.forms[experiment.selected_id]

  const get_outcome_plate_matrix = () => make_plate_matrix(rows, columns,
    (x, y) => outcome_well_object({ x: x, y: y }))

  const [plate_matrix, set_plate_matrix] = useState(get_outcome_plate_matrix())

  return (
    <div id="plateContainer" >
      <table>
        <thead>
          <tr className='outcome_plate_row'>
            <th></th>
            {get_int_array(columns).map((column_id) => (
              <th key={column_id} scope='column'>{column_id + 1}</th>
            ))}
          </tr>
        </thead>
        <tbody key={experiment.selected_id}>
          {plate_matrix.map((rowElement, row) => (
            <tr key={row} className="input_row">
              <td className="row_label">{alph[row]}</td>
              {rowElement.map((well_object, column) => (
                <td key={(row + 1) + ((column) * rows)}  >
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
export default PureOutcomePlate
