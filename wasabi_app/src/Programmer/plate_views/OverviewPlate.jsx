import { useContext } from "react"
import { alph } from "../utils"
import { AppGlobalContext } from '@src/AppGlobalContext.jsx';
function OverviewPlate(props) {
  const { experiment, set_experiment } = useContext(AppGlobalContext)
  const rows = experiment.plateDimensions.rows
  const columns = experiment.plateDimensions.columns
  const selected_form = experiment.forms[experiment.selected_id]

  const plate = () => {
    const plate_well_array = [];
    for (let row = 0; row < rows; row++) {
      for (let column = 0; column < columns; column++) {
        const id = `${alph[row]}${column + 1}`
        plate_well_array.push({
          id: id,
          volume: 0
        })
      }
    }
    return plate_well_array 
  }
  return <> full overview plate </>
}

export default OverviewPlate
