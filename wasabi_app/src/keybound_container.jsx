import { useEffect } from "react"
import { useRef } from "react"
import { useState } from "react"

function Keybound_Container({ children, function_map, update_keystate }) {
  const function_library = useRef({})

  useEffect(() => {
    if (!function_map) { return }
    for (const [keybind, function_bind] of function_map) {
      const strKey = keybind.toSorted().toString()
      function_library.current[strKey] = function_bind
    }
  }, [function_map])


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
    set_active_keys(prev => {
      if (!prev.includes(event.key)) {
        return [...prev, event.key]
      }
      return prev
    })
    call_by_actives()
  }

  const keyup_handler = (event) => {
    const filtered_keys = active_keys.filter((keyname) => keyname !== event.key)
    set_active_keys(filtered_keys)
  }

  useEffect(() => {

    window.addEventListener('keydown', keydown_handler);
    window.addEventListener('keyup', keyup_handler);

    return () => {
      window.removeEventListener('keydown', keydown_handler);
      window.removeEventListener('keyup', keyup_handler);
    };
  }, [])


  useEffect(() => {
    console.log("keystate changed: ", active_keys)
    update_keystate(active_keys)
  }, [active_keys])

  return (
    <div
      onKeyDown={keydown_handler}
      onKeyUp={keyup_handler}
    >
      {children}
    </div>)
}
export default Keybound_Container
