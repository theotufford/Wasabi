import { useState, useRef, useEffect  } from 'react'
import PlateElement from './plateElement.jsx'
import InstructionForm from './InstructionForm.jsx'
import './programmer.css'
import LegendElement from './legend.jsx'
import ApiElement from './flaskApi'
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

  useEffect(() => {
    console.log("i was called on first Render!")
    return () => {
      console.log('i am a cleanup function')
    }
  }, [])

const [experiment, setExperiment] = useState({
  plateDimensions: {
    rows:8,
    columns:12
  },
  formArray: [{
    id:0
  }],
  colorMap:new Map(),
  version:0,
})
  function tmpFormArr() {
    const tmp = experiment.formArray.map(_ => _) // structured clone except it tolerates functions
    return(tmp)
  }

  const setPlateDimensions = (value) => {
    setExperiment(prev => ({...prev, plateDimensions:value}))
  } 
  const setformArray = (value) => {
    setExperiment(prev => ({...prev, formArray:value}))
  } 
  const setColorMap = (value) => {
    setExperiment(prev => ({...prev, colorMap:value}))
  } 
  const setTitle = (value) => {
    setExperiment(prev => ({...prev, title:value}))
  } 

  const titleChange = (event) => {
    const newTitle = event.target.value
    setTitle(newTitle)
  }

  let liveColorMap = new Map()
  let deadColorSet = new Set()

  const initPlateMatrix = []
  for (let row = 0; row <= experiment.plateDimensions.rows; row++) {
    const rowArray = []
    for( let column = 1; column <= experiment.plateDimensions.columns; column++){
      rowArray.push({
        id:`${alph[row]}${column}`,
        formAttachmentData:[],
        color:'', 
        colorHandler: function(currentformArray) {
          if(!this.formAttachmentData || this.formAttachmentData.length === 0){
            this.color = ''
            return -1
          }
          // sort to avoid keying errors associated with insertion order carrying into value of string 
          const sortedFormAttachmentData = this.formAttachmentData.sort((a,b) => a - b) // this is javascript for "sort in ascending order", which is stupid
          const formComboStringKey = JSON.stringify(sortedFormAttachmentData)
          if (liveColorMap.has(formComboStringKey)){
            this.color = liveColorMap.get(formComboStringKey)
          } else {
            const newColor = getColor()
            liveColorMap.set(formComboStringKey, newColor)
            deadColorSet.add(newColor)
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
            setColorMap(liveColorMap)
            this.color = newColor
            deadColorSet = deadColorSet.difference(new Set([newColor]))
            return {deadColorSet:deadColorSet, liveColorMap:liveColorMap} 
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
            console.log("hasId error: ", error)
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
    const parsedFrom = alphNumToCoords(formObject.from.toLowerCase())
    const parsedTo = alphNumToCoords(formObject.to.toLowerCase())


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
      outCoordRange.upperBound.x > experiment.plateDimensions.columns ||
      outCoordRange.upperBound.y > experiment.plateDimensions.rows
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
      console.log('invalid range!')
      return -1
    }
    const cornerRange = formattedRange.range 
    formObject.area = cornerRange.area

    let colorHandlerResponse;
    const added = []
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
            added.push(wellElement.id) 
          }
        } 
        colorHandlerResponse = wellElement.colorHandler(experiment.formArray)
      })
    })
    if (colorHandlerResponse === -1) {
      return
    }

    setPlateMatrix(mutablePlateMatrix)
    console.log('set plate materix')
  }

  const modifyFormArray = (formObject) => {
    if (experiment.formArray [formObject.id]) {
      const tmp = tmpFormArr()
      tmp[formObject.id] = formObject
      setformArray ([...tmp])
    } else {
      setformArray ([...experiment.formArray , formObject])
    }
  }

  const addEmptyForm = () => {
    const latestForm = experiment.formArray [experiment.formArray .length - 1]
    const emptyForm = {
     id:(latestForm.id+1)
    }
    modifyFormArray (emptyForm)
  }

  const deleteForm = (id) => {
    const shortenedFormArray = tmpFormArr().filter((form) => {
      const isntForm = form.id !== id
      console.log('filtering')
      return isntForm
    })
    setformArray(shortenedFormArray)
  }




  return (
    <div id = "experiment">
    <div id="forms">
    <input type="text" name="experimentTitle" onChange = {titleChange} placeholder = "insert title"/>
    {experiment.formArray.map((form) => (
    <div key = {form.id} className="instructionForm">
      <InstructionForm 
        id = {form.id}
        rangeHandler = {rangeHandler}
        modifyFormArray = {modifyFormArray}
        deleteForm = {deleteForm}
      />
    </div>
  ))}
    <button type="submit" onClick = {addEmptyForm}> add form </button>
    <button type="button" onClick = {deleteForm}> save experiment</button>
    </div>
    <div id = "visualElements">
    <PlateElement plateMatrix = {plateMatrix}/>
    <LegendElement formArray = {experiment.formArray} colorMap = {experiment.colorMap}/>
    </div>
    <ApiElement experiment = {experiment} />
    </div>
  )
}

export default Programmer
