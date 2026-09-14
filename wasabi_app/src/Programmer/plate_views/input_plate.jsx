import { useContext, useEffect, useState } from 'react';
import { AppGlobalContext } from '@src/AppGlobalContext.jsx';
import { useRef } from 'react';
import { alph, make_plate_matrix, for_2d, alph_to_coords, coords_to_alph, get_int_array, get_well_array_from_corners, map_2d, alph_sort, get_id_set } from '../utils.jsx';

const get_new_well_obj = (row, column, volume_map = {}) => {
  const well_id = coords_to_alph(column, row)
  return {
    id: well_id,
    volume: volume_map[well_id] | 0
  }
}


function InputPlate(props) {
  const { keystate, set_keybind_function_map, experiment, set_experiment, mouse_state } = useContext(AppGlobalContext)
  const rows = experiment.plateDimensions.rows
  const columns = experiment.plateDimensions.columns
  const selected_form = experiment.forms[experiment.selected_id]
  const id_set = get_id_set(rows, columns)
  const get_input_plate_matrix = () => make_plate_matrix(rows, columns,
    (x, y) => get_new_well_obj(y, x, selected_form.volume_map))

  const [plate_matrix, set_plate_matrix] = useState(get_input_plate_matrix())

  const update_volume_map = (id, volume) => set_experiment(prev => {
    const clone_exp = structuredClone(prev)
    const selected_form_clone = clone_exp.forms[clone_exp.selected_id]
    selected_form_clone.volume_map[id] = volume
    return clone_exp
  })

  const verify_focused_wrapper = (callback) => (...args) => {
    const active = document.activeElement
    if (active.className === 'well-input') {
      callback(...args)
    }
  }

  useEffect(() => {
    set_keybind_function_map(new Map([
      [[" "], blur_all],
      [["Escape"], blur_all],
      [["Enter"], blur_all],
      [["Control", "a"], select_all]
    ]))
    return () => {
      set_keybind_function_map(new Map())
    };
  }, [])

  useEffect(() => {
    set_plate_matrix(get_input_plate_matrix())
  }, [selected_form.volume_map])

  const parse_sheet_paste = (str) => {
    const input_rows = str.split(" ")
    return input_rows.map(
      (row_string) => row_string.split(/[ \t ; , ]/)
        .map((cell_value) => parseFloat(cell_value) || 0)
    )
  }

  const cascade_sheet_input = (initial_well_element, value) => {
    const parsed_volume_matrix = parse_sheet_paste(value)
    const width = parsed_volume_matrix[0].length
    const height = parsed_volume_matrix.length
    const initial = alph_to_coords(initial_well_element.id)

    for_2d(initial.x, initial.y, width, height, (x, y) => {
      const volume_value = parsed_volume_matrix[y][x]
      const target_wellid = coords_to_alph(x, y)
      update_volume_map(target_wellid, volume_value)
    })

  }

  const selected_wellids = useRef(new Set())
  const last_well_selected = useRef("")


  const select_all = verify_focused_wrapper(() => {
    selected_wellids.current = id_set
    const all_cells = Array.from(document.getElementsByClassName("input-cell"))
    all_cells.forEach(element => (element.classList.add("selected")))
    last_well_selected.current = "A1"
    document.getElementById("A1").focus()
  })

  const blur_all = () => {
    id_set.forEach((id) => document.getElementById(id).classList.remove("selected"))
    selected_wellids.current = new Set()
    last_well_selected.current = ""
    document.activeElement?.blur()
  }

  const select_sub_range = (corner_1, corner_2) => {
    const initial_selected = new Set(selected_wellids.current)
    const new_id_set = new Set(get_well_array_from_corners(corner_1, corner_2))
    selected_wellids.current = new_id_set
    const needs_html_select_class_updated = initial_selected.symmetricDifference(selected_wellids.current)
    needs_html_select_class_updated.forEach((id) => {
      document.getElementById(id).classList.toggle("selected")
    })
  }

  const handle_well_select = (event) => {
    if (keystate.current.includes("Shift") && last_well_selected.current !== "") {
      select_sub_range(event.target.id, last_well_selected.current)
    } else {
      last_well_selected.current = event.target.id
    }
  }

  const handle_well_input = (event) => {
    const input_val = event.target.value
    if (input_val.includes(" ") || input_val.includes("\n")) {
      cascade_sheet_input(event.target, input_val)
      return
    }
    const value = parseFloat(input_val) || 0
    selected_wellids.current.forEach((id) => {
      update_volume_map(id, value)
    })
  }


  const handle_mousedown = (event) => {
    event.preventDefault();
    blur_all()
    const id = event.target.id
    last_well_selected.current = id
  }
  const handle_mouseup = (event) => {
    event.target.select()
  }

  const handle_mouseover = (event) => {
    if (mouse_state.current == 1) {
      const corner_2_id = event.target.id
      const corner_1_id = last_well_selected.current
      if (corner_1_id !== corner_2_id) {
        select_sub_range(corner_1_id, corner_2_id)
      }
    }
  }

  const container_ref = useRef(null)
  const click_deselect_handler = (event) => {
    const container = container_ref.current
    const target = event.target
    const contains_target = container.contains(target)
    if (container === null) { return }
    if (!contains_target) {
      blur_all()
    }
  }
  useEffect(() => {
    window.addEventListener("click", click_deselect_handler)
    return () => {
      window.removeEventListener("click", click_deselect_handler)
    };
  }, [])



  return (
    <div ref={container_ref} id="plateContainer" >
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
                  <div id={element.id} className="unselected input-cell">
                    <input
                      className='well-input'
                      defaultValue={element.volume || null}
                      key={element.volume}
                      id={element.id}
                      placeholder='0'
                      onMouseDown={handle_mousedown}
                      onPointerMove={handle_mouseover}
                      onMouseUp={handle_mouseup}
                      autoFocus={last_well_selected.current == element.id}
                      onChange={handle_well_input}
                      onFocus={handle_well_select}
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
  )
}

export default InputPlate
