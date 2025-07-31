import { useState } from 'react'
const alph = 'abcdefghijklmnopqrstuvwxyz' 
import { useEffect } from 'react';


function SubElement(props) {
  const [range, setRange] = useState({from:{col:0, row:0}, to:{col:0, row:0}})
  useEffect(() => {
    props.clickHandler(range);
  }, [range]);
  const setCorner = () => {
    const alphVal = alph.indexOf(event.target.value[0])
    const num = event.target.value.slice(1)
    const corner = event.target.name
    const update = {}
    update[corner] = {row:alphVal, col:num}
    setRange(currentRange => ({
      ...currentRange,
      ...update
    }))
  }
  return (
    <div id = {props.id}>
      <input type="text" name="from" placeholder = "from" onChange = {setCorner}/>
      <input type="text" name="to" placeholder = "to" onChange = {setCorner}/>
    </div>
  )
}
export default SubElement
