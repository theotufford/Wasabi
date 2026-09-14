import { useState, useRef, useEffect, useContext } from 'react'
import { AppGlobalContext } from './AppGlobalContext.jsx'
import Dropdown_Search from './dropdown_input.jsx'
import "./Reagent_Selector.css"

import { apiCall, add_new_reagent, delete_reagent as db_delete_reagent, modify_reagent } from './backendConfig.jsx'

class Reagent_lib {
  constructor(initialization_callback, previous_lib = undefined) {
    console.log("given lib: ", previous_lib)
    this.lib = new Object(previous_lib)
    this.initialization_callback = initialization_callback
    if (!previous_lib) {
      if (!this.cached_lib) {
        apiCall({
          route: "dump_reagents"
        }).then((resp) => {
          this.lib = resp.data
          this.cache_current_lib()
        }).then(() => (initialization_callback(this)));

      } else {
        this.lib = this.cached_lib
        initialization_callback(this)
      }
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

  cache_current_lib() {
    if (this.lib == undefined) {
      return
    }
    localStorage.setItem("reagent_lib", JSON.stringify(this.lib))
  }
  get cached_lib() {
    const cache_result = localStorage.getItem("reagent_lib")
    if (cache_result === "undefined" || cache_result === undefined) {
      return undefined
    }
    return JSON.parse(cache_result)
  }
  new_reagent(reagent_name, meta = {}) {
    add_new_reagent(reagent_name, meta)
    this.lib[reagent_name] = meta
    this.cache_current_lib()
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


export function Reagent_Selector({ selected_reagent, select_reagent, enable_creation = true }) {

  const [reagent_lib_state, set_reagent_lib_state] = useState()
  const [view_state, set_view_state] = useState("display_reagent")

  useEffect(() => {
    new Reagent_lib(set_reagent_lib_state)
  }, [])

  if (view_state === "dropdown") {
    return <div>
      <Dropdown_Search
        autoFocus={true}
        placeholder="input reagent name"
        select_option_source={reagent_lib_state?.names}
        defaultValue={selected_reagent}
        onSelect={(event) => {
          select_reagent(event.target.value)
          set_view_state("display_reagent")
        }}>
        {enable_creation ?
          <button command="show-modal" commandfor='new-reagent-input-modal'>input new reagent</button>
          : <></>}
      </Dropdown_Search>
      {enable_creation ?
        <New_Reagent_Modal select_reagent={select_reagent} lib_obj={reagent_lib_state} />
        : <></>
      }
    </div>
  }
  if (view_state === "display_reagent") {
    return <div>
      {selected_reagent}
      <button onClick={() => {set_view_state("dropdown")}}>change reagent</button>
    </div>
  }
}
