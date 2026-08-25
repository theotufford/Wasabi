import { useContext, useEffect, useState } from 'react';
import { ExperimentContext } from '../ExperimentContext.jsx';
import WellElement from './wellElement.jsx'
import { useRef } from 'react';
import Color_plate_map from './color_plate_map.jsx';
import "./css/plate.css"
import InputPlate from './input_plate.jsx';
import Volume_display_plate from './volume_display_plate.jsx';

// range select
// range common input
// csv copy / paste
// csv drag / drop
// per-reagent view that triggers sim

export default function PlateElement(props) {
  const { experiment, set_experiment } = useContext(ExperimentContext)
  const [experiment_reagents, set_experiment_reagents] = useState([])
  const new_reagents = []
  Object.values(experiment.forms).forEach((form) => {
    console.log("considering form: ", experiment_reagents)
    const reagent = form?.reagent
    if (reagent == undefined) {
      return
    }
    if (experiment_reagents.includes(reagent)) {
      return
    }
    if (new_reagents.includes(reagent)) {
      return
    }
    new_reagents.push(reagent)
  })
  if (new_reagents.length != 0) {
    set_experiment_reagents((prev) => ([...prev, ...new_reagents]))
  }
  const [view_mode, set_view_mode] = useState("color tree view")
  const view_options = {
    "color tree view": <Color_plate_map {...props} />,
  }

  experiment_reagents.forEach((reagent) => {
    console.log("reagent found: ", reagent)
    view_options[`${reagent} total volume`] = < Volume_display_plate reagent={reagent} />
  })

  const selected_form = experiment.forms[experiment.selected_id]
  const is_direct_input = selected_form?.is_direct_input ? selected_form.is_direct_input : false

  if (is_direct_input) {
    view_options["direct input"] = <InputPlate />
  }

  const view_set_button = (e) => {
    const view_name = e.target.name
    set_view_mode(view_name)
  }

  const [selected_wells, set_selected_wells] = useState([])

  return (
    <div>
      <div id='plate_view'>
        {view_options[view_mode]}
      </div>
      <div>
        {Object.keys(view_options).map((view_name) => (
          <button name={view_name} onClick={view_set_button}>{view_name}</button>
        ))}
      </div>
    </div>
  )

}
