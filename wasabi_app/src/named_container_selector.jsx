import { useState, useRef, useEffect, useContext } from 'react'
import { AppGlobalContext } from './AppGlobalContext.jsx'
import Dropdown_Search from './dropdown_input.jsx'
import apiCall, { control_call } from './backendConfig.jsx'

export function Container_selector({ selected_container, select_container }) {
  const [view_state, set_view_state] = useState("display_reagent")

  if (view_state === "dropdown") {
    return <div>
      dropdown goes here
      <Dropdown_Search
        autoFocus={true}
        placeholder="input name"
        select_option_source={reagent_lib_state?.names}
        defaultValue={""}
        onSelect={(event) => {
          select_container(event.target.value)
        }} />
    </div>
  }

  if (view_state === "display_reagent") {
    return <div>
      {selected_container}
      <button onClick={() => { set_view_state("dropdown") }}>⌄</button>
    </div>
  }
}
