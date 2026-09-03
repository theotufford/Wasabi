import { useState, useRef, useEffect, useContext } from 'react'
import { AppGlobalContext } from './AppGlobalContext.jsx'
import Dropdown_Search from './dropdown_input.jsx'
import "./Reagent_Selector.css"

import { apiCall, add_new_reagent, delete_reagent as db_delete_reagent, modify_reagent } from './backendConfig.jsx'

class Reagent_lib {
  constructor(initialization_callback, previous_lib = undefined) {
    this.lib = new Object(previous_lib)
    this.initialization_callback = initialization_callback
    if (!previous_lib) {
      apiCall({
        route: "dump_reagents"
      }).then((resp) => { this.lib = resp.data })
        .then(() => (initialization_callback(this)));
    } else {
      initialization_callback(this)
    }
  }
  get names() {
    if (!this.lib) {
      return undefined
    }
    return Object.keys(this.lib)
  }
  new_reagent(reagent_name, meta = {}) {
    add_new_reagent(reagent_name, meta)
    this.lib[reagent_name] = meta
    this.update_state()
  }
  delete_reagent(reagent_name) {
    delete this[reagent_name]
    db_delete_reagent(reagent_name)
    this.update_state()
  }
  store_reagent_change(name) {
    modify_reagent(name, this.lib[name])
  }
  update_state() {
    new Reagent_lib(this.initialization_callback, this.lib)
  }
}

function New_Reagent_Modal({ select_reagent, lib_obj }) {
  return (
    <dialog id='new-reagent-input-modal'>
      <form className="new-reagent-form" action={(data) => {
        const name = data.get("reagent-name")
        lib_obj.new_reagent(name, {})
        select_reagent(name)
        document.getElementById("new-reagent-input-modal").close()
      }}>
        shorthand name for search: <input name="reagent-name" />
        description: <textarea type='text' name='description' />
        <button type="submit">submit</button>
      </form>
    </dialog >
  )
}


export function Reagent_Selector({ selected_reagent, select_reagent }) {
  const [reagent_lib_state, set_reagent_lib_state] = useState()

  useEffect(() => {
    new Reagent_lib(set_reagent_lib_state)
  }, [])

  return <>
    <Dropdown_Search
      placeholder="input reagent name"
      select_option_source={reagent_lib_state?.names}
      defaultValue={selected_reagent}
      onSelect={(event) => select_reagent(event.target.value)}>
      <button command="show-modal" commandfor='new-reagent-input-modal'>input new reagent</button>
    </Dropdown_Search>
    <New_Reagent_Modal select_reagent={select_reagent} lib_obj={reagent_lib_state} />
  </>
}
