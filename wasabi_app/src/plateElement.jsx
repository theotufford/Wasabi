import { useContext, useEffect, useState } from 'react';
import { ExperimentContext } from './experiment_context.jsx';
import WellElement from './wellElement.jsx'
import { useRef } from 'react';

const alph = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split('')

function coords_to_alph(x, y) {
  return `${alph[y]}${x + 1}`
}
function alph_to_coords(str) {
  const x = parseInt(str.slice(1), 10) - 1
  const y = alph.indexOf(str[0])
  if (Number.isNaN(x) || y === -1) {
    return -1
  }
  return {
    x: x,
    y: y
  }
}

const alph_corners_to_ordered_coords = (corner_1, corner_2) => {
  corner_1 = alph_to_coords(corner_1)
  corner_2 = alph_to_coords(corner_2)

  if (corner_1 === -1 || corner_2 === -1) {
    return undefined
  }

  let lower_x
  let lower_y
  let upper_x
  let upper_y

  if (corner_1.x > corner_2.x) {
    upper_x = corner_1.x
    lower_x = corner_2.x
  } else {
    upper_x = corner_2.x
    lower_x = corner_1.x
  }
  if (corner_1.y > corner_2.y) {
    upper_y = corner_1.y
    lower_y = corner_2.y
  } else {

    upper_y = corner_2.y
    lower_y = corner_1.y
  }
  return [{ x: lower_x, y: lower_y }, { x: upper_x, y: upper_y }]
}

const get_well_array_from_corners = (corner_1, corner_2) => {
  const well_arr = []
  const [lower, upper] = alph_corners_to_ordered_coords(corner_1, corner_2)
  for (let x_coord = lower.x; x_coord <= upper.x; x_coord++) {
    for (let y_coord = lower.y; y_coord <= upper.y; y_coord++) {
      well_arr.push(coords_to_alph(x_coord, y_coord))
    }
  }
  console.log("got well array: ", well_arr)
  return well_arr
}

function PlateElement(props) {
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

  const get_empty_plate_matrix = () => {
    const tmp_plate_matrix = [];
    for (let row = 0; row < rows; row++) {
      const row_array = []
      for (let column = 0; column < columns; column++) {
        row_array.push({
          id: `${alph[row]}${column + 1}`,
          forms_attached: [],
          color: '',
        })
      }
      tmp_plate_matrix.push(row_array)
    }
    return tmp_plate_matrix
  }


  const [plate_matrix, set_plate_matrix] = useState(get_empty_plate_matrix())
  useEffect(() => {
    const tmp = get_empty_plate_matrix()
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
    let current_form
    Object.entries(experiment.forms).forEach(([id, form]) => {
      if (form.is_selected) {
        current_form = form
      }
    })
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
    tmp[current_form.id] = { ...structuredClone(tmp[current_form.id]), well_array: Array.from(wells) }
    set_experiment(prev => ({ ...prev, forms: tmp }))
  }

  return (
    <div id="plateContainer">
      {plate_matrix.map((rowElement, row) => (
        <div key={row} className="plateRow">
          {rowElement.map((element, column) => (
            <WellElement onClick={handle_well_click} {...plate_matrix[row][column]} key={column} />
          ))}
        </div>
      ))}
    </div>
  )
}
export default PlateElement
