import { useContext, useEffect, useState } from 'react';
import { ExperimentContext } from '@src/ExperimentContext.jsx';
import { useRef } from 'react';
import { alph, alph_to_coords, get_int_array } from '../utils.jsx';
import Keybound_Container from '@src/keybound_container.jsx';

const get_volume_map = (plate_matrix) => {
  let linearized = []
  plate_matrix.forEach((row) => {
    linearized = [...linearized, ...row]
  })
  const output = {}
  linearized.forEach((well_element) => {
    output[well_element.id] = well_element.volume
  })
  return output
}

function InputPlate(props) {
  const { experiment, set_experiment } = useContext(ExperimentContext)
  const rows = experiment.plateDimensions.rows
  const columns = experiment.plateDimensions.columns
  const selected_form = experiment.forms[experiment.selected_id]

  const get_initial_plate_matrix = (rows, columns) => {
    const empty_plate_matrix = [];
    for (let row = 0; row < rows; row++) {
      const row_array = []
      for (let column = 0; column < columns; column++) {
        const id = `${alph[row]}${column + 1}`
        const volume = selected_form?.volume_map?.[id] || 0
        row_array.push({
          id: id,
          volume: volume
        })
      }
      empty_plate_matrix.push(row_array)
    }
    return empty_plate_matrix
  }

  const [plate_matrix, set_plate_matrix] = useState(get_initial_plate_matrix(rows, columns))

  useEffect(() => {
    set_plate_matrix(get_initial_plate_matrix(rows, columns))
  }, [experiment.selected_id])




  const set_well_volume = (wellid, volume) => {
    const { x, y } = alph_to_coords(wellid)
    const current_volume = plate_matrix[y][x].volume
    if (current_volume === volume) {
      return
    }
    const modified_plate_matrix = structuredClone(plate_matrix)
    modified_plate_matrix[y][x] = { id: wellid, volume: volume }
    set_plate_matrix(modified_plate_matrix)
  }

  const reverting = useRef(false)
  const plate_history = useRef([plate_matrix])
  const plate_history_ind = useRef(0)

  const undo = () => {
    reverting.current = true
    plate_history_ind.current = (plate_history_ind.current - 1) % 30;
    const target_state = plate_history[plate_history_ind]
    if (target_state == undefined) {
      plate_history_ind.current += 1
      return
    }
    set_plate_matrix(target_state)
  }

  const redo = () => {
    reverting.current = true
    plate_history_ind.current = (plate_history_ind.current + 1) % 30;
    const target_state = plate_history[plate_history_ind]
    if (target_state == undefined) {
      plate_history_ind.current -= 1
      return
    }
    set_plate_matrix(target_state)
  }

  const update_volume_map = () => {
    set_experiment(prev => ({
      ...prev,
      forms: {
        ...prev.forms,
        [prev.selected_id]: {
          ...prev.forms[prev.selected_id],
          volume_map: get_volume_map(plate_matrix)
        }
      }
    }))
  }
  useEffect(() => {
    update_volume_map()
    if (reverting == true) {
      reverting.current = false
      return
    }

    plate_history_ind.current = (plate_history_ind.current + 1) % 30;
    plate_history.current[plate_history_ind] = plate_matrix
    for (let i = plate_history_ind.current; i < plate_history.current.length; i++) {
      plate_history.current[i] = undefined
    }

  }, [plate_matrix])

  const selected_inputs = useRef([])

  const space_blur = () => {
    document.activeElement?.blur();
  }

  const keybinds_map = new Map([
    [["Control", "z"], undo],
    [["Control", "y"], redo],
    [[" "], space_blur],
  ])

  const handle_well_input = (event) => {
    const input_val = event.target.value
    const value = parseFloat(input_val) || 0
    set_well_volume(event.target.id, value)
  }

  const keystate = useRef([])

  const handle_well_select = (event) => {
    selected_inputs.current[0] == event.target.id
    // if (keystate.current.includes("Shift")) {
    // }
  }


  return (
    <Keybound_Container ext_keystate={keystate} function_map={keybinds_map}>
      <div id="plateContainer">
        <table>
          <thead>
            <tr className='input_row'>
              <th> </th>
              {get_int_array(columns).map((column_id) => (
                <th key={column_id} scope='column'>{column_id + 1}</th>
              ))}
            </tr>
          </thead>
          <tbody key={experiment.selected_id}>
            {plate_matrix.map((rowElement, row) => (
              <tr key={row} className="input_row">
                <td className="row_label">{alph[row]}</td>
                {rowElement.map((element, column) => (
                  <td key={(row + 1) + ((column) * rows)}  >
                    <div className='input_cell'>
                      <input
                        inputMode='numeric'
                        step="any"
                        defaultValue={element.volume || null}
                        key={element.volume}
                        id={element.id}
                        placeholder='0'
                        onFocus={handle_well_select}
                        onBlur={handle_well_input}
                      />
                      <span className='units-span'>μL</span>
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Keybound_Container>
  )
}

export default InputPlate
