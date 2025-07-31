import { useState } from 'react'
import WellElement from './wellElement.jsx'
const alph = "abcdefghijklmnopqrstuvwxyz".split('')

// dependencies: 
// rows, columns
// color map object 

function PlateElement(props){

  const plateMatrix = props.plateMatrix

  return (
    <div id = "plateContainer">
    { plateMatrix.map((rowElement,row) => (
      <div key = {row} class = "plateRow">
      { rowElement.map((element,column) => (
          <WellElement {...plateMatrix[row][column]} key = {column}/>
      ))}
      </div>
    ))}
    </div>
  )
}
export default PlateElement
