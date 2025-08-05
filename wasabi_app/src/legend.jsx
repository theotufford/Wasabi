import { useState } from 'react'
import { useEffect } from 'react';
import InstructionForm from './InstructionForm.jsx'
import './legend.css'

const diffBlockDefault = {
  width: "2vw",
  height: "1vh"
}
const keyDefault ={
  display: "flex",
  flexFlow: "column nowrap",
  margin: "2vw",
  justifyContent: "center"

}

function LegendElement(props) {
  const experiment = props.formArray
  const [legend, setLegend] = useState([<div> empty </div>])
  const updateLegend = () => {
    const colorMap = props.colorMap
    const keyArray = Array.from(colorMap.keys())
    const formKeySets = keyArray.map( (formKeyString) => (new Set(JSON.parse(formKeyString))) )

    let sizeSeparatedKeySets = []

    formKeySets.forEach((keySet) => {
      const keySize = keySet.size
      if (!sizeSeparatedKeySets[keySize]) {
        sizeSeparatedKeySets[keySize] = []
      }
      sizeSeparatedKeySets[keySize].push(keySet)
    })

    sizeSeparatedKeySets = sizeSeparatedKeySets.filter(set => set) // remove empty indexes, shortening the list to its order 

    if (sizeSeparatedKeySets.length < 1) {
      return
    }

    const minKeySize = sizeSeparatedKeySets[0][0].size // grab smallest key size (useful if for all the wells have n contents where n>1)
    const desc_siSepKeySets = sizeSeparatedKeySets.reverse(); // set order descending 
    const sizeCount = desc_siSepKeySets.length

    const tree = new Map()
    const renderedBranches = []

    const defaultRender = (args) => {
    const diffColor = args.diffColor
    const selfColor = args.selfColor
    const addingSymbol = diffColor?['', '']:'' 
    const info = args.info
    const children = args.children ? <div class = 'children'> {args.children.map((child) => (child?.html))} </div> :''
      return(
      <div key = {selfColor} style = {{...keyDefault, border:'solid', borderColor: selfColor}} class = 'keyContainer'> 
        <div class = 'keyBase'>
        { addingSymbol[0]} <div class="diffColorBlock" style = {{...diffBlockDefault, backgroundColor:diffColor}} />
        {addingSymbol[1]}{info}
        <div class="selfColorBlock" style = {{backgroundColor:selfColor}} /> 
        </div>
        {children}
      </div>
      )
    }
    desc_siSepKeySets.forEach((layer, layerIndex) => {
      if (layerIndex > sizeCount) {
        console.log('no parents found and len not min size ? basically how did this key get here: ', layer)
        return
      }
      const nextLayer = desc_siSepKeySets.length === 1 ? desc_siSepKeySets[0] : desc_siSepKeySets[layerIndex+1]
      keyLoop: for (const keySet of layer) {
        const color = colorMap.get(JSON.stringify([...keySet]))
        const branch = tree.get(keySet)
        if (keySet.size === minKeySize) {
          let singlet_info = '';
          for (const formIndex of [...keySet]) {
            const form = experiment[formIndex]
            singlet_info += `${form.method} volume of ${form.reagent}\n`
          }
          const renderData = { info:singlet_info, selfColor: color, children: branch?.children }
          const render = defaultRender(renderData)
          tree.set(keySet, {
            html: render, 
            children:branch?.children
          })
          renderedBranches.push(render)
          continue
        }
        if (!nextLayer) {
          return
        }

        for (const smallerKey of nextLayer) {
          if (smallerKey.isSubsetOf(keySet)) {

            let info = ''
            let children = [];

            if (branch) {
              children = branch.children
            }

            const diffKeys = keySet.difference(smallerKey)
            const diffColor = colorMap.get(JSON.stringify([...diffKeys]))

            for (const formIndex of [...diffKeys]) {
              const form = experiment[formIndex]
              info += `${form.method} volume of ${form.reagent}\n`
            }

            const keySetHtml = defaultRender({
              diffColor: diffColor,
              info : info, 
              children:children,
              selfColor:color
            })

            tree.set(keySet, {
              html:keySetHtml,
              children:children
            }) 

            const newBranch = tree.get(keySet)

            let parent = tree.get(smallerKey)
            if (!parent) {
              tree.set(smallerKey, {children:[]})
              parent = tree.get(smallerKey)
            }
            parent.children.push(newBranch)
            continue keyLoop;
          }
        }
        nextLayer.push(keySet)
      }
    })
    return renderedBranches
  }
  useEffect(() => {
    setLegend([])
    const html = updateLegend()
    if (!html) {
      return
    }
    console.log('updateLegend')
    setLegend(html)
  }, [experiment])
  return (
    <div class = "legendContainer">
    {legend.map((legendBranch) =>  (legendBranch) )}
    </div>
  )
}


export default LegendElement
