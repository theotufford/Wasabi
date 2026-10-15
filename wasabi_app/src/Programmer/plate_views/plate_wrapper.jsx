import { useContext, useEffect, useState } from 'react';
import { AppGlobalContext } from '@src/AppGlobalContext.jsx';
import { useRef } from 'react';
import { alph, make_plate_matrix, get_int_array, get_well_array_from_corners, get_id_set, coords_to_alph, alph_corners_to_ordered_coords, alph_sort } from '../utils.jsx';

function Plate_Wrapper({ well_constructor, value_map, update_value_map }) {
  const { keystate, set_keybind_function_map, experiment, set_experiment, mouse_state } = useContext(AppGlobalContext)
  const rows = experiment.plateDimensions.rows
  const columns = experiment.plateDimensions.columns
  const id_set = get_id_set(rows, columns)
  const get_plate_matrix = (valmap) => make_plate_matrix(rows, columns, well_constructor, valmap)


  const [plate_matrix, set_plate_matrix] = useState(get_plate_matrix())


  const verify_focused_wrapper = (callback) => (...args) => {
    const active = document.activeElement
    if (active.className.includes('well')) {
      callback(...args)
    }
  }

  useEffect(() => {
    set_keybind_function_map(new Map([
      [[" "], clear_selection],
      [["Escape"], clear_selection],
      [["Enter"], clear_selection],
      [["Control", "a"], select_all]
    ]))
    return () => {
      set_keybind_function_map(new Map())
    };
  }, [])

  const [selected_wellids, set_selected_wellids] = useState(new Set())
  const sort_counter = useRef(0)
  useEffect(() => {
    if (sort_counter.current == 0) {
      set_selected_wellids(new Set(alph_sort(Array.from(selected_wellids))))
      console.log("sorted: ", selected_wellids)
    }
    sort_counter.current += 1
    sort_counter.current %= 2
  }, [selected_wellids])

  useEffect(() => {
    set_plate_matrix(get_plate_matrix(value_map))
  }, [value_map])



  const select_all = () => {
    set_selected_wellids(id_set)
    let first_nonempty_cell = ""
    id_set.forEach((id) => {
      if (document.getElementById(id).value != "" && first_nonempty_cell == "") {
        first_nonempty_cell = id
      }
    })
    if (first_nonempty_cell == "") { first_nonempty_cell = "A1" }
    document.getElementById(first_nonempty_cell).focus()
    
  }

  const clear_selection = verify_focused_wrapper(() => {
    set_selected_wellids(new Set())
    corner_index.current = 0
    corner_select.current = ["", ""]
    document.activeElement?.blur()
  })

  const select_sub_range = (corner_1, corner_2) => {
    const new_id_set = new Set(get_well_array_from_corners(corner_1, corner_2))
    set_selected_wellids(new_id_set)
    document.getElementById(corner_2).focus()
  }

  const corner_select = useRef(["", ""])
  const corner_index = useRef(0)

  const last_selected = () => { return corner_select.current[corner_index.current] }

  const explicit_select = (wellid) => {
    if (last_selected() == wellid) { return }
    corner_select.current[corner_index.current] = wellid
    if (corner_index.current == 1) {
      select_sub_range(corner_select.current[0], corner_select.current[1])
      corner_index.current = 0
    } else {
      set_selected_wellids(new Set([wellid]))
    }
    document.getElementById(wellid).focus()
  }

  const apply_to_all_selected = (event) => {
    const new_value = event.target.value
    selected_wellids.forEach((id) => {
      update_value_map(id, new_value)
    })
  }

  const handle_mousedown = (event) => {
    event.preventDefault();
    clear_selection()
    explicit_select(event.target.id)
  }
  const handle_mouseup = (event) => {
    explicit_select(event.target.id)
    corner_index.current = 0
  }

  const handle_mouseover = (event) => {
    if (mouse_state.current == 1) {
      if (corner_select.current[0] != "") {
        corner_index.current = 1
        explicit_select(event.target.id)
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
      clear_selection()
    }
  }
  useEffect(() => {
    window.addEventListener("click", click_deselect_handler)
    return () => {
      window.removeEventListener("click", click_deselect_handler)
    };
  }, [])



  return (
    <div ref={container_ref}
      id="plateContainer"
      autoFocus={selected_wellids.size > 0}
    >
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
            <tr key={row} className="plate_row">
              <td className="row_label">{alph[row]}</td>
              {rowElement.map((Well_constructor, column) => (
                <td key={(row + 1) + ((column) * rows)}  >
                  <Well_constructor
                    onMouseDown={handle_mousedown}
                    onPointerMove={handle_mouseover}
                    onMouseUp={handle_mouseup}
                    change_callback={apply_to_all_selected}
                    autoFocus={last_selected() == coords_to_alph(column, row)}
                    selected={selected_wellids.has(coords_to_alph(column, row))}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default Plate_Wrapper
