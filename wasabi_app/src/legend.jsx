import { useState } from 'react'
import { useEffect } from 'react';
import InstructionForm from './InstructionForm.jsx'
import './legend.css'
function LegendElement(props) {
  const formArray = props.formArray
  const [legend, setLegend] = useState({'initial':{html:'empty'}})
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

    sizeSeparatedKeySets = sizeSeparatedKeySets.filter(set => set).reverse(); // remove empty indexes and set order descending 

    const keyHeap = new Map()

    sizeSeparatedKeySets.forEach((layer, layerIndex) => {
      const nextLayer = sizeSeparatedKeySets.length === 1 ? sizeSeparatedKeySets[0] : sizeSeparatedKeySets[layerIndex+1]
      layer.forEach((keySet) => {
        const baseValueObject = {
            selfKey: keySet,
            closestParent: new Set(),
            color: colorMap.get(JSON.stringify([...keySet])),
        }
        if (!keyHeap.get(keySet)){
          keyHeap.set(keySet, baseValueObject) 
        }
        if (keySet.size === 1) {
          return
        }
        if (!nextLayer) {
          return
        }
        nextLayer.forEach((compKey) => {
          if (compKey.isSubsetOf(keySet)) {
            const addedKeySetValue = keySet.difference(compKey)
            let addedColor;
            let realKeySet;
            for (const keySet of colorMap.keys()) {
              const setsAreIdentical = addedKeySetValue.difference(keySet).size === 0
              if (setsAreIdentical) {
                addedColor = colorMap.get(keySet)
                realKeySet = keySet
              }
            }
            const formIds = [...realKeySet]
            let info = '+ '
            for (const formId of formIds) {
              const form = experiment[formId]
              info += `${form.method} volume of ${form.reagent}\n`
            }

            const addedElement = (
              <div class = 'additionContainer' >
              <div class = 'verticalSpanColorBlock' style = {{backgroundColor:addedColor}}>
              </div>
              <p class = 'additionInfoText'>{info}</p>
              </div>
            )
            keyHeap.set(keySet, {
              ...baseValueObject,
              closestParent:compKey,
              addedElement: addedElement
            })
          }
        })
      })
    })


    const descendingSizeColorKeys = Array.from(keyHeap.keys()).sort((key1, key2) => (key2.size - key1.size))
    const getHtml = () => {
      if (descendingSizeColorKeys.length === 0) {
          console.log('0 return')
        return (
          <div>
          hi  
          </div>
        )
      }
      const tree = new Map()
      //console.log('keyHeap: ', keyHeap)
      //console.log('orderedKeys', descendingSizeColorKeys)
      for (const keyHeapKey of descendingSizeColorKeys){
        const keyHeapValue = keyHeap.get(keyHeapKey)
        let path = []
        let currentParentObj = keyHeap.get(keyHeapValue.closestParent) 
        if (!currentParentObj) {
          keyHeapValue.isMapped = true
          tree.set(keyHeapValue.selfKey, path)
          continue
        }
        //console.log('initiating mapping loop on ', currentParentObj)
        while (true){
          //console.log(currentParentObj)
          if (currentParentObj.isMapped) {
            path = path.reverse();
            if (!tree.get(currentParentObj.selfKey)) {
              tree.set(currentParentObj.selfKey, [path])
              break
            }
            tree.get(currentParentObj.selfKey).push([path])
            break
          }
          if (currentParentObj.selfKey.size === 1) {
            path.push(currentParentObj.selfKey)
            path = path.reverse();
            currentParentObj.isMapped = true
            tree.set(keyHeapValue.selfKey, [path])
            break
          }
          path.push(currentParentObj.selfKey)
          currentParentObj.isMapped = true
          currentParentObj = keyHeap.get(currentParentObj.closestParent)
        }
        console.log(tree)
      }

      let rootKey = Array.from(tree.keys())[0];
      let loopCount = 0

      while (true) {
        loopCount++;
        if (loopCount > 9999) break; 
        const root = tree.get(rootKey)
        const keyHeapObj = keyHeap.get(rootKey)
        console.log('root -> ', root)
        const selfColor = root.color
        let info = '' 
        for (const formID of keyHeapObj.selfKey) {
          const form = formArray[formID]
          info += `${form.method} volume of ${form.reagent}\n`
        }
        if (!root.html) {
          root.html = {
            branchHtml : [],
            rendered: (
              <div>
              <div class = "legendAdded">
              {keyHeap.get(selfKey)?.addedHtml}
              </div>
              <div class = "legendMain" style = {{backgroundColor: selfColor}}></div>
              <div class="branchHtml">
              { (() => 
                ( if (branchHtml.length > 0) (
                  branchHtml.map(
                    (branch) => (
                      branch?.html?.rendered
                  )
                )))
              )()} </div>
              </div>
            )
          }
        }
        console.log('in legend rending loop, ', loopCount, '\nroot: ', root)
        branchLoop: for (const branchPath of root) {
          if (!root.length || root?.rendered) {
            rootKey = root.backRootKey
            break
          }
          // if for every branch in branchpath, branch.isRendered, root = backroot 
          // else, for every branch in branchPath, root.html.append(renderedhtml)
          // renderedHtml looks like
          /*
            <div>
            <div>
              root html
            </div>
            <div>
              map root.htmlArray
                if branch of root has renderedHtml, return rendered 
                else: render based on data 
            </div>
            </div>
          */
          if (root?.rendered) {
            rootKey = root.backRootKey
            break
          }
          for (const branch of branchPath) {
            const subBranch = tree.get(branch.selfKey)
            if (subBranch?.length === 0) {
            }
            if (subBranch) {
              branch.backRootKey = rootKey
              rootKey = branch.selfKey 
              break branchLoop
            }
          }
        }
      }
    }
    getHtml()
  }

  useEffect(() => {
    updateLegend()
  }, [formArray])

  return (
    <div>
    </div>
  )



//  return (
//    <div class = "legendContainer">
//    {legend.reverse().map((layer, index) => {
//      return (
//        <div class = {`legendRowContainer`} key = {layer.mapKey}>
//        layer: {index}
//        {
//          layer.map((legendObject) => {
//            return (
//              <div  key = {legendObject.primaryColor} style = {{margin: '1.25vw'}}>
//              <div class="parentColorBox" style = {{backgroundColor:legendObject.primaryColor, width: '2vw', height: '2vw'}}>
//              </div>
//
//              {legendObject.info}
//
//              <div class = 'childColorContainer'>
//              {legendObject.childColors.map((color) => (
//                <div key = {color} style = {{backgroundColor: color, width: '2vw', height: '2vw'}}>
//                </div>
//              ))}
//              </div>
//              </div>
//            )
//          })
//        }
//        </div>
//      )})}
//    </div>
//  )
}

export default LegendElement
