import { useState, useRef, useEffect, useContext } from 'react'
import PlateElement from './plate_element.jsx'
import { motion } from 'motion/react';
import InstructionForm from './InstructionForm.jsx'
import { v4 as uuidv4 } from 'uuid';
import SaveButton from './SaveButton.jsx';
import './css/Programmer.css'
import { control_call } from '@src/backendConfig.jsx';
import { AppGlobalContext, default_form } from '@src/AppGlobalContext.jsx';




function Draggable_box({ children, ...props }) {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-zinc-900 overflow-hidden">
      <motion.div
        drag="y"
        dragMomentum={false}
        dragSnapToOrigin={true}
        whileHover={{ scale: 1.05 }}
        dragElastic={0.2}
        whileTap={{ scale: 0.95, cursor: 'grabbing' }}
        {...props}
      >
        {children}
      </motion.div>
    </div>
  );
}


function Programmer(props) {
  const { experiment, set_experiment } = useContext(AppGlobalContext)
  const modify_experiment = (key, value) => {
    set_experiment(previous_value => ({ ...previous_value, [key]: value }))
  }
  const setTitle = (value) => {
    modify_experiment("title", value)
  }
  const addEmptyForm = () => {
    const tmp = structuredClone(experiment)
    const form_index = Object.keys(experiment.forms).length
    const empty_form = { ...default_form, id: uuidv4(), index: form_index }
    tmp.forms[experiment.selected_id].is_selected = false
    tmp.forms[empty_form.id] = empty_form
    tmp.selected_id = empty_form.id
    set_experiment(tmp)
  }

  const order_forms = (event) => {
    const form_bound_entries = Object.keys(experiment.forms).map((form_key) => {
      const form_drag_box = document.getElementById(form_key)
      return [form_drag_box.getBoundingClientRect(), form_key]
    })
    console.log("bounds: ", form_bound_entries)
    const comparator = (a, b) => {
      const box_a = a[0]
      const box_b = b[0]
      const b_middle = box_b.top - box_b.height / 2
      return box_a.top - b_middle
    }
    form_bound_entries.sort(comparator)
    const tmp = structuredClone(experiment)
    const sorted_forms = {}
    form_bound_entries.forEach(([box, key], index) => {
      tmp.forms[key].index = index
      sorted_forms[key] = tmp.forms[key]
    })
  console.log("sorted forms", sorted_forms)
   tmp.forms = sorted_forms
   set_experiment(tmp)
  }

  const keydownHandler = (event) => {
    if (["Enter", "Escape"].includes(event.key)) {
      event.target.blur()
    }
  }


  return (
    <div id="experiment">
      <div id="instruction-input">
        <div className="title-row">
          <input
            type="text"
            key={experiment.title}
            name="experimentTitle"
            defaultValue={experiment.title}
            onBlur={(event) => setTitle(event.target.value)}
            onKeyDown={keydownHandler}
            placeholder="experiment title"
          />
          <span className="version-label">v{experiment.version}</span>
        </div>
        <div className="form-actions">
          <SaveButton />
        </div>
        <div className="forms">
          {Object.keys(experiment.forms).map((form_id) => (
            <Draggable_box onDragEnd={order_forms} id={form_id}>
              <InstructionForm
                id={form_id}
                key={form_id}
              />
            </Draggable_box>
          ))}
        </div>
        <button className="add-form-btn" onClick={addEmptyForm}>+ add instruction</button>
      </div>
      <div id="visualElements">
        <PlateElement />
      </div>
    </div>
  )
}
export default Programmer
