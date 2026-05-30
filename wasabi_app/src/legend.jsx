import { useState } from 'react'
import { useEffect } from 'react';
import './legend.css'

const diffBlockDefault = {
  width: "2vw",
  height: "1vh"
}

const keyDefault = {
  display: "flex",
  flexFlow: "column nowrap",
  margin: "0.5vw",
  justifyContent: "center"
}
const defaultRender = (args) => {
  const diffColor = args.diffColor
  const selfColor = args.selfColor
  const addingSymbol = diffColor ? ['', ''] : ''
  const info = args.info
  const children = args.children ? <div className='children'> {args.children.map((child) => (child?.html))} </div> : ''
  return (
    <div key={selfColor} style={{ ...keyDefault, border: 'solid', borderColor: selfColor }} className='keyContainer'>
      <div className='keyBase'>
        {addingSymbol[0]} <div className="diffColorBlock" style={{ ...diffBlockDefault, backgroundColor: diffColor }} />
        {addingSymbol[1]}{info}
        <div className="selfColorBlock" style={{ backgroundColor: selfColor }} />
      </div>
      {children}
    </div>
  )
}

function LegendElement(props) {
  const forms = props.experiment.forms
  console.log("called legend element refresh: ", props)
  const color_lib = props.color_lib
  const keyArray = Array.from(color_lib.keys(color_lib))

  // map string type keys for color combos to sets of form uuids
  const formKeySets = keyArray.map((formKeyString) => (new Set(JSON.parse(formKeyString))))
  console.log("keys: ", formKeySets)

  // put key sets into size ranked 2d array where each size of key set
  // has one sub array that contains all the key sets of that size
  let keysBySize = []
  formKeySets.forEach((keySet) => {
    // console.log("handling keySet ", keySet)
    const keySize = keySet.size
    if (!keysBySize[keySize]) {
      keysBySize[keySize] = []
    }
    keysBySize[keySize].push(keySet)
  })

  keysBySize = keysBySize.filter(set => set) // remove empty indexes, shortening the list to its order 


  if (keysBySize.length == 0) {
    return
  }

  const min_key_len = keysBySize[0][0].size // grab smallest key size (useful if for all the wells have n contents where n>1)
  const keySets = keysBySize.reverse(); // set order descending in size

  const tree = new Map()
  const renderedBranches = []

  console.log("handling legend tree generation with:", keySets)
  keySets.forEach((layer, layerIndex) => {
    if (layerIndex > keySets.length) {
      console.log('no parents found and len not min size ? basically how did this key get here: ', layer)
      return
    }

    const nextLayer = keySets.length == 1 ? keySets[0] : keySets[layerIndex + 1]

    keyLoop: for (const keySet of layer) {
      // grab color from keyset
      const stringKey = JSON.stringify([...keySet])
      const color = color_lib.get(stringKey)

      const branch = tree.get(keySet)
      if (keySet.size === min_key_len) {
        let singlet_info = '';
        for (const formIndex of [...keySet]) {
          const form = forms[formIndex]
          singlet_info += `${form.method} volume of ${form.reagent}`
        }
        const renderData = { info: singlet_info, selfColor: color, children: branch?.children }
        const render = defaultRender(renderData)
        tree.set(keySet, {
          html: render,
          children: branch?.children
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
          const diffColor = color_lib[JSON.stringify([...diffKeys])]

          for (let formIndex of [...diffKeys]) {
            const form = forms[formIndex]
            info += `${form.method} volume of ${form.reagent} \n`
          }

          const keySetHtml = defaultRender({
            diffColor: diffColor,
            info: info,
            children: children,
            selfColor: color
          })

          tree.set(keySet, {
            html: keySetHtml,
            children: children
          })

          const newBranch = tree.get(keySet)

          let parent = tree.get(smallerKey)
          if (!parent) {
            tree.set(smallerKey, { children: [] })
            parent = tree.get(smallerKey)
          }
          parent.children.push(newBranch)
          continue keyLoop;
        }
      }
      nextLayer.push(keySet)
    }
  })

  return (
    <div className="legendContainer">
      {renderedBranches.map((legendBranch) => (legendBranch))}
    </div>
  )
}


export default LegendElement
