import { useState } from 'react'
import SubElement from './Test_subElement.jsx'

function Test() {
  const dimensions = {x:3,y:5}
  const initMatrix = []
  for (let row = 0; row <= dimensions.y; row++) {
    const rowArray = []
    for( let column = 0; column<=dimensions.x; column++){
      rowArray.push(0);
    }
    initMatrix.push(rowArray)
  }
  const [matrix, setMatrix] = useState(initMatrix)
  const alph = 'abcdefghijklmnopqrstuvwxyz'.split('')

  const setRange = (range) => {
    const tmpMatrix = matrix.map(row => [...row]); 
    for (let row = 0; row <= dimensions.y; row++) {
      for (let column = 0; column <= dimensions.x; column++) {
        if (
          row >= range.from.row &&
          row <= range.to.row &&
          column >= range.from.col &&
          column <= range.to.col
        ) {
          tmpMatrix[row][column] = 2;
        }
      }
    }
    setMatrix(tmpMatrix); 
    console.log('range: ', tmpMatrix);
  };

  return (
    <div>
    { matrix.map((rowElement,row) => (
      <div key = {row}>
      { rowElement.map((element,column) => (
          <div id = {`${alph[row]}${column}`} color = {props.wellColorDaemon[row][column]} key = {column}>
        {alph[row]}{column} : {matrix[row][column]} 
          </div>
      ))}
      </div>
    ))}
    < SubElement clickHandler = {setRange}/>
    </div>
  )
}
export default Test
