import { useContext, useRef, useEffect, useState } from 'react';
import { AppGlobalContext } from '@src/AppGlobalContext.jsx';
import Plate_Wrapper from './plate_wrapper.jsx';

const Well_Element = (props) => {
  props.defaultValue = props.value
  delete props.value
  const classes = props.selected ? "input-cell selected" : "input-cell"

  return (
    <div className={classes}>
      <input
        className='well-input'
        key={props.defaultValue}
        placeholder='0'
        onChange={props.change_callback}
        {...props}
      />
      <span className='units-span'>μL</span>
    </div>
  )
}


function InputPlate(props) {
  const { experiment, set_experiment } = useContext(AppGlobalContext)
  const selected_form = experiment.forms[experiment.selected_id]

  const update_volume_map = (id, volume) => set_experiment(prev => {
    const clone_exp = structuredClone(prev)
    const selected_form_clone = clone_exp.forms[clone_exp.selected_id]
    selected_form_clone.volume_map[id] = volume
    return clone_exp
  })

  const volume_map = selected_form.volume_map

  return <Plate_Wrapper well_constructor={Well_Element} value_map={volume_map} update_value_map={update_volume_map} />
}

export default InputPlate
