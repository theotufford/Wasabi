import { useState } from 'react'
import { useEffect } from 'react';
import PlateElement from './plateElement.jsx'
import InstructionForm from './InstructionForm.jsx'
import './programmer.css'
import LegendElement from './legend.jsx'
const alph = "abcdefghijklmnopqrstuvwxyz".split('')

const staticColorLibrary = [
  "Red",
  "Blue",
  "Yellow",
  "DarkViolet",
  "HotPink",
  "Turquoise",
  "DarkRed",
  "LawnGreen",
  "DarkBlue",
  "DarkOrange",
]; //thanks chatgpt XD
function getColor() {
  const picked = staticColorLibrary.pop();
  return picked;
}
function alphNumToCoords(idString){
    let x = parseInt(idString.slice(1),10)
    const y = alph.indexOf(idString[0])
  if (Number.isNaN(x) || y === -1) {
    return -1
  }
  x--; // accounts for 0,0 being a1 rather than a0
  return {
    x:x,
    y:y
  }
}
function Programmer(){

  const [plateDimensions, setPlateDimensions] = useState({
    rows:8,
    columns:12
  })
  const [colorMap, setColorMap] = useState(new Map())
  const liveColorMap = new Map()

  const initPlateMatrix = []
  for (let row = 0; row <= plateDimensions.rows; row++) {
    const rowArray = []
    for( let column = 1; column <= plateDimensions.columns; column++){
      rowArray.push({
        id:`${alph[row]}${column}`,
        formAttachmentData:[],
        color:'', 
        colorHandler: function(currentformArray) {
          // need to sort to avoid keying errors associated with insertion order
          if(!this.formAttachmentData || this.formAttachmentData.length === 0){
            return -1
          }

          const sortedFormAttachmentData = this.formAttachmentData.sort((a,b) => a - b) // this is javascript for "sort in ascending order", which is stupid
          const formComboStringKey = JSON.stringify(sortedFormAttachmentData)
          if (liveColorMap.has(formComboStringKey)){
            this.color = liveColorMap.get(formComboStringKey)
          } else {

            const newColor = getColor()
            liveColorMap.set(formComboStringKey, newColor)
            setColorMap(prevColorMap => new Map([...prevColorMap, [formComboStringKey, newColor]]))

            sortedFormAttachmentData.forEach((id) => {
              currentformArray .forEach((formObject) => {
                if (formObject.id === id) {
                  if (!formObject.colors) {
                    formObject.colors = [newColor]
                  }
                  if(formObject.colors.indexOf(newColor) === -1){
                    formObject.colors.push(newColor)
                  }
                }
              })
            })
            this.color = newColor
            return newColor 
          }
        },
        deleteId: function(id) {
          const forms = this.formAttachmentData
          const idIndex = forms.indexOf(id)
          if ( idIndex === -1) {
            return -1
          }
          forms.splice(idIndex,1)
        },
        hasId: function(id) {
          let outBool = false
          try {
            const hasId = (this.formAttachmentData.indexOf(id) !== -1) 
            outBool = hasId
          } catch (error) {
            console.log("hasId error: ",error)
          }
          return outBool
        }, 
        addId: function(id){
          this.formAttachmentData.push(id)
        }
      })
    }
    initPlateMatrix.push(rowArray)
  }
  const [plateMatrix, setPlateMatrix] = useState(initPlateMatrix)
  const orderFromTo = (formObject) => {
    const parsedFrom = alphNumToCoords(formObject.from)
    const parsedTo = alphNumToCoords(formObject.to)


    if (parsedFrom === -1 || parsedTo === -1) {
      return {invalid:true}

    }

    const outCoordRange = {
      lowerBound:{},
      upperBound:{}
    }

    if (parsedFrom.x > parsedTo.x) {
      outCoordRange.upperBound.x = parsedFrom.x
      outCoordRange.lowerBound.x = parsedTo.x
    } else {
      outCoordRange.upperBound.x = parsedTo.x
      outCoordRange.lowerBound.x = parsedFrom.x
    } 
    if (parsedFrom.y > parsedTo.y) {
      outCoordRange.upperBound.y = parsedFrom.y
      outCoordRange.lowerBound.y = parsedTo.y
    } else{

      outCoordRange.upperBound.y = parsedTo.y
      outCoordRange.lowerBound.y = parsedFrom.y
    }

    const outOfBounds = (
      outCoordRange.lowerBound.x < 0 ||
      outCoordRange.lowerBound.y < 0 ||
      outCoordRange.upperBound.x > plateDimensions.columns ||
      outCoordRange.upperBound.y > plateDimensions.rows
    )

    if (outOfBounds) {
      return {invalid:true} 
    }


    return {orderedValues:outCoordRange, invalid:false}
  }

  const getRange = (formObject) => {
    const formattedCorners = orderFromTo(formObject)

    if (formattedCorners.invalid){
      return {invalid:true}
    }
    const lowerBound = formattedCorners.orderedValues.lowerBound 
    const upperBound = formattedCorners.orderedValues.upperBound
    const area = (upperBound.x - lowerBound.x) * (upperBound.y - lowerBound.y)
    const plateMatrix_subRange = [] 
    for (let row = lowerBound.y; row <= upperBound.y; row++){
      plateMatrix_subRange[row] = []
      for (let column = lowerBound.x; column <= upperBound.x; column++){
        plateMatrix_subRange[row][column] = plateMatrix[row][column]
      }
    }
    return {range: plateMatrix_subRange, area:area, invalid:false};
  }

  const rangeHandler = (formObject) => {
    const mutablePlateMatrix = plateMatrix.map((row) => ([...row]))
    const formattedRange = getRange(formObject)
    if (formattedRange.invalid) {
      return -1
    }
    const cornerRange = formattedRange.range 
    formObject.area = cornerRange.area
    mutablePlateMatrix.forEach((rowObject, row) => {

      rowObject.forEach((wellElement, column) => {
        const subRange_row = cornerRange[row]
        let cornerRange_wellElement = false  
        wellElement.deleteId(formObject.id)
        if (subRange_row) {
          cornerRange_wellElement = subRange_row[column]
          if (!cornerRange_wellElement) {
          } else if (!wellElement.hasId(formObject.id)){
            wellElement.addId(formObject.id)
          }
        } 
        wellElement.colorHandler(formArray)
      })
    })
    setPlateMatrix(mutablePlateMatrix)
  }

  const modifyFormArray = (formObject) => {
    if (formArray [formObject.id]) {
      const tmpArrObj = formArray .map((form) => (form))
      tmpArrObj[formObject.id] = formObject
      setformArray ([...tmpArrObj])
    } else {
      setformArray ([...formArray , formObject])
    }
  }

  const [formArray , setformArray ] = useState([{
    id:0
  }])

  const addEmptyForm = () => {
    const latestForm = formArray [formArray .length - 1]
    const emptyForm = {
     id:(latestForm.id+1)
    }
    modifyFormArray (emptyForm)
  }

  

  const [experiment, setExperiment] = useState({plate:plateDimensions, forms:formArray, colorMap:colorMap})

  return (
    <div id = "experiment">
    <div id="forms">
    {formArray.map((form) => (
    <div key = {form.id} class="instructionForm">
      <InstructionForm id = {form.id} rangeHandler = {rangeHandler} modifyFormArray = {modifyFormArray} />
    </div>
  ))}
    <button type="submit" onClick = {addEmptyForm}></button>
    </div>
    <div id = "visualElements">
    <PlateElement plateMatrix = {plateMatrix}/>
    <LegendElement formArray = {formArray} colorMap = {colorMap}/>
    </div>
    </div>
  )
}

export default Programmer
