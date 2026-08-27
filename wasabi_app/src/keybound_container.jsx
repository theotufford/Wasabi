import { useEffect } from "react"
import { useRef } from "react"
import { useState } from "react"

function get_alph_sort(arr) {
  console.log("arr: ", arr)
  return arr.toSorted((a, b) => a.localeCompare(b))
}

function Keybound_Container({ children, function_map, ext_keystate }) {
  const function_library = useRef({})

  useEffect(() => {
    for (const [keybind, function_bind] of function_map) {
      const strKey = keybind.toSorted().toString()
      function_library.current[strKey] = function_bind
    }
  }, [])


  const [active_keys, set_active_keys] = useState([])

  const call_by_actives = () => { }

  useEffect(() => {

    if (active_keys.length == 0) {
      return
    }
    const active_keys_strKey = active_keys.toSorted().toString()
    const successful_call = function_library.current[active_keys_strKey]?.()
  }, [call_by_actives])

  const keydown_handler = (event) => {
    if (!active_keys.includes(event.key)) {
      set_active_keys(prev => [...prev, event.key])
      ext_keystate.current = [...active_keys, event.key]
    }
    call_by_actives()
  }

  const keyup_handler = (event) => {
    const filtered_keys = active_keys.filter((keyname) => keyname != event.key)
    set_active_keys(filtered_keys)
    ext_keystate.current == filtered_keys
  }

  return (
    <div
      onBlur={() => { set_active_keys([]) }}
      onKeyDown={keydown_handler}
      onKeyUp={keyup_handler}>
      {children}
    </div>)
}

export default Keybound_Container
