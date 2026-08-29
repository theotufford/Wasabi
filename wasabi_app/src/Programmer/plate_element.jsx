import { useContext, useEffect, useState } from 'react';
import SelectPlate from './plate_views/select_plate.jsx';
import { ExperimentContext } from '@src/ExperimentContext.jsx';
import OverviewPlate from './plate_views/OverviewPlate.jsx';
import { useRef } from 'react';
import "./css/plate.css"
import InputPlate from './plate_views/input_plate.jsx';
import PureOutcomePlate from './plate_views/pure_outcome_plate.jsx';
import Impure_Input_Plate from './plate_views/impure_input_plate.jsx';

// range select
// range common input
// csv copy / paste
// csv drag / drop
// per-reagent view that triggers sim

export default function PlateElement(props) {
  const { experiment, set_experiment } = useContext(ExperimentContext)
  const selected_form = experiment.forms[experiment.selected_id]
  const default_options = { "overview": <OverviewPlate />, "": <>loading...</> }
  const [view_options, set_view_options] = useState(default_options)
  const [view_mode, set_view_mode] = useState("")

  useEffect(() => {
    const method_meta = selected_form.method_meta
    let new_options = default_options
    if (method_meta.is_direct_input) {
      new_options = {
        ...new_options,
        "input": <InputPlate />
      }
      set_view_mode("input")
    }
    if (method_meta.has_region_select) {
      new_options = {
        ...new_options,
        "": <SelectPlate />,
        "outcome": (method_meta.purity == "pure" ?
          <PureOutcomePlate /> :
          <Impure_Input_Plate />
        )
      }
      set_view_mode("")
    }
    set_view_options(new_options)
  }, [selected_form.method_meta])

  const view_set_button = (e) => {
    const view_name = e.target.name
    set_view_mode(view_name)
  }

  return (
    <div>
      <div id='plate_view'>
        {view_options[view_mode]}
      </div>
    </div>
  )

}
