import WellElement from './wellElement.jsx'
function PlateElement(props){
  const plateMatrix = props.plateMatrix
  return (
    <div id = "plateContainer">
    { plateMatrix.map((rowElement,row) => (
      <div key = {row} className = "plateRow">
      { rowElement.map((element,column) => (
          <WellElement {...plateMatrix[row][column]} key = {column}/>
      ))}
      </div>
    ))}
    </div>
  )
}
export default PlateElement
