import { useEffect, useState } from 'react';
import WellElement from './wellElement.jsx'

const alph = "abcdefghijklmnopqrstuvwxyz".split('')

function alphNumToCoords(str) {
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

const get_range = (formObject) => {
  const from_input = formObject.from
  const to_input = formObject.to

  if (!from_input || !to_input) {
    return undefined
  }
  const from = alphNumToCoords(from_input)
  const to = alphNumToCoords(to_input)


  if (from === -1 || to === -1) {
    return undefined
  }
  const outCoordRange = {
    lowerBound: {},
    upperBound: {}
  }

  if (from.x > to.x) {
    outCoordRange.upperBound.x = from.x
    outCoordRange.lowerBound.x = to.x
  } else {
    outCoordRange.upperBound.x = to.x
    outCoordRange.lowerBound.x = from.x
  }
  if (from.y > to.y) {
    outCoordRange.upperBound.y = from.y
    outCoordRange.lowerBound.y = to.y
  } else {

    outCoordRange.upperBound.y = to.y
    outCoordRange.lowerBound.y = from.y
  }
  return outCoordRange
}

function PlateElement(props) {
  const rows = props.experiment.plateDimensions.rows
  const columns = props.experiment.plateDimensions.columns
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
    const form_array = Object.keys(props.experiment.forms)
    form_array.forEach((form_id) => {
      const form = props.experiment.forms[form_id]
      const plate_range = get_range(form)
      if (plate_range) {
        const lowerBound = plate_range.lowerBound
        const upperBound = plate_range.upperBound
        for (let row = lowerBound.y; row <= upperBound.y; row++) {
          for (let column = lowerBound.x; column <= upperBound.x; column++) {
            const well = tmp[row][column]
            if (!well) {
              // TODO add security to this so people dont silent error keep impossible well ranges
              continue
            }
            well.forms_attached.push(form_id)
          }
        }
      }
    })

    const color_lib = new Map();
    for (let row = 0; row < rows; row++) {
      for (let column = 0; column < columns; column++) {
        const well = tmp[row][column]
        const forms = Array.from(well.forms_attached).sort()
        if (forms.length == 0) { continue }
        const string_key = JSON.stringify(forms)
        if (color_lib.get(string_key) == undefined) {
          color_lib.set(string_key, getColor())
        }
        well.color = color_lib.get(string_key)
      };
    }

    set_plate_matrix(tmp)
    props.set_color_lib(color_lib)

  }, [props.experiment.forms])


  return (
    <div id="plateContainer">
      {plate_matrix.map((rowElement, row) => (
        <div key={row} className="plateRow">
          {rowElement.map((element, column) => (
            <WellElement {...plate_matrix[row][column]} key={column} />
          ))}
        </div>
      ))}
    </div>
  )
}
export default PlateElement
