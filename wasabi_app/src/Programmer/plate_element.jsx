import { useContext, useEffect, useState } from 'react';
import SelectPlate from './plate_views/select_plate.jsx';
import { AppGlobalContext } from '@src/AppGlobalContext.jsx';
import OverviewPlate from './plate_views/OverviewPlate.jsx';
import { useRef } from 'react';
import "./css/plate.css"
import InputPlate from './plate_views/input_plate.jsx';
import PureOutcomePlate from './plate_views/pure_outcome_plate.jsx';
import Impure_Outcome_plate from './plate_views/impure_outcome_plate.jsx';

// range select
// range common input
// csv copy / paste
// csv drag / drop
// per-reagent view that triggers sim

function PlateElement(props) {
  const { experiment, set_experiment } = useContext(AppGlobalContext)
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
        "select_plate": <SelectPlate />,
        "outcome_plate": (method_meta.purity == "pure" ?
          <PureOutcomePlate /> :
          <Impure_Outcome_plate />
        )
      }
      set_view_mode("select_plate")
    }
    set_view_options(new_options)
  }, [selected_form.method_meta])

  return (
    <div>
      <div key={view_mode} id='plate_view'>
        {view_options[view_mode]}
      </div>
       <select value = {view_mode} onChange={(ev) => { set_view_mode(ev.target.value) }} >
        {Object.keys(view_options).map((view_name) => {
          if ( view_name == "" ) return
          return <option value={view_name}>{view_name}</option>
        })}
      </select>
    </div>
  )
}

export default PlateElement
