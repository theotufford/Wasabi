import { useEffect } from "react";
import { useRef } from "react";
import { useState } from "react";
import "./Dropdown_Search.css"


function filter_options_with_input(options, input) {
  if (!input) {
    return options.slice(0,3)
  }
  const inp = input.toLowerCase()
  const new_valid_options = options.filter((option_val) => {
    const opt = option_val.toLowerCase()
    const validity = opt.includes(inp)
    return validity
  })

  return new_valid_options
}

export default function Dropdown_Search({
  select_option_source = [],
  defaultValue = undefined,
  placeholder = "",
  onSelect,
  children,
}) {
  const [input_value, set_input_value] = useState(defaultValue)
  const [valid_options, set_valid_options] = useState(select_option_source.slice(0,3))
  const [dropdown_visibility, set_dropdown_visibility] = useState("hidden")

  const handle_option_select = (event) => {
    set_input_value(() => event.target.value)
    onSelect(event)
  }

  useEffect(() => {
    set_valid_options(() => filter_options_with_input(select_option_source, input_value))
  }, [input_value])

  return <div>
    <input
      className="dropdown-input"
      placeholder={placeholder}
      value={input_value}
      onInput={(event) => { set_input_value(event.target.value) }}
      onFocus={() => { set_dropdown_visibility("") }}
    />
    <div className={dropdown_visibility}>
      <div className="dropdown_options_container">
        top 3 options:
        {valid_options.map((valid_option) => (
          <button className="dropdown_option" onClick={handle_option_select} value={valid_option}>{valid_option}</button>
        ))}
        {children}
      </div>
    </div>
  </div>
}
