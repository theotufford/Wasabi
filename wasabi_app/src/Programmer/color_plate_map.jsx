import { useContext, useEffect, useState } from 'react';
import { ExperimentContext } from '../ExperimentContext.jsx';
import WellElement from './wellElement.jsx'
import { useRef } from 'react';
import { alph_sort, alph, get_well_array_from_corners } from './utils.jsx';

function Color_plate_map(props) {
  const { experiment, set_experiment } = useContext(ExperimentContext)
  const rows = experiment.plateDimensions.rows
  const columns = experiment.plateDimensions.columns
  const staticColorLibrary = [
    "Red",
    "Blue",
    "Yellow",
    "DarkViolet",
    "HotPink",
    "Turquoise",
    "DarkRed",
    "LawnGreen",
    "DarkBlue",
    "DarkOrange",
  ];

  function getColor() {
    const picked = staticColorLibrary.pop();
    return picked;
  }

  const get_empty_plate_matrix = (rows, columns) => {
    const empty_plate_matrix = [];
    for (let row = 0; row < rows; row++) {
      const row_array = []
      for (let column = 0; column < columns; column++) {
        row_array.push({
          id: `${alph[row]}${column + 1}`,
          forms_attached: [],
          color: '',
        })
      }
      empty_plate_matrix.push(row_array)
    }
    return empty_plate_matrix
  }

  const [plate_matrix, set_plate_matrix] = useState(get_empty_plate_matrix(rows, columns))

  useEffect(() => {
    const tmp = get_empty_plate_matrix(rows, columns)
    const form_array = Object.keys(experiment.forms)
    form_array.forEach((form_id) => {
      const form = experiment.forms[form_id]
      const well_array = form?.well_array
      if (!well_array) {
        return
      }
      for (let row = 0; row < rows; row++) {
        for (let column = 0; column < columns; column++) {
          const well = tmp[row][column]
          if (well_array.includes(well.id)) {
            well.forms_attached.push(form_id)
          }
        }
      }
    })
    const color_lib = new Map();
    for (let row = 0; row < rows; row++) {
      for (let column = 0; column < columns; column++) {
        const well = tmp[row][column]
        const form_ids = Array.from(well.forms_attached).sort()
        if (form_ids.length == 0) { continue }
        const string_key = JSON.stringify(form_ids)
        if (color_lib.get(string_key) == undefined) {
          color_lib.set(string_key, getColor())
        }
        well.color = color_lib.get(string_key)
      };
    }

    set_plate_matrix(tmp)
    props.set_color_lib(color_lib)

  }, [experiment])

  const select_group = useRef({ corner_1: "", corner_2: "" })

  const handle_well_click = (click_event) => {
    const current_form = experiment.forms[experiment.selected_id]
    click_event.preventDefault()
    const target_id = click_event.currentTarget.id
    let wells = new Set([target_id])
    const current_wells = new Set(current_form.well_array)
    if (select_group.current.corner_1 != "" && click_event.shiftKey) {
      select_group.current.corner_2 = target_id
      const selected_range = new Set(get_well_array_from_corners(select_group.current.corner_1, select_group.current.corner_2))
      wells = current_wells.union(selected_range)
    } else {
      if (click_event.ctrlKey) {
        if (!current_wells.has(target_id)) {
          wells = wells.union(current_wells)
        } else {
          wells = current_wells.difference(wells)
        }
      }
      select_group.current.corner_1 = target_id
      select_group.current.corner_2 = target_id
    }
    const tmp = structuredClone(experiment.forms)
    const well_array = alph_sort(Array.from(wells))

    tmp[current_form.id] = { ...structuredClone(tmp[current_form.id]), well_array: well_array }
    set_experiment(prev => ({ ...prev, forms: tmp }))
  }

  return (
    <div id="plateContainer">
      {plate_matrix.map((rowElement, row) => (
        <div key={row} className="color_plate_row">
          {rowElement.map((element, column) => (
            <WellElement onClick={handle_well_click} {...plate_matrix[row][column]} key={column} />
          ))}
        </div>
      ))}
    </div>
  )
}
export default Color_plate_map
