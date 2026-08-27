export const alph = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split('')

export function get_int_array(n){
  return Array.from({ length: n}, (_, i) => i)
}

export function coords_to_alph(x, y) {
  return `${alph[y]}${x + 1}`
}
export function alph_to_coords(str) {
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

export function alph_corners_to_ordered_coords(corner_1, corner_2) {
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


export function get_well_array_from_corners(corner_1, corner_2) {
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

// top left to bottom right sorting of a linear well array
export function alph_sort(well_array){
  const alph_compare = (alph1, alph2) => {
    const coord1 = alph_to_coords(alph1)
    const coord2 = alph_to_coords(alph2)
    if (coord1.y > coord2.y) return 1
    if (coord1.y < coord2.y) return -1

    // implicit else y1 = y2
    if (coord1.x > coord2.x) return 1
    else return -1
  }
  return well_array.sort(alph_compare)
}
