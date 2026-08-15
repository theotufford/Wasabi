import { useState, useRef, useEffect, useContext } from 'react'
import { ExperimentContext } from './ExperimentContext.jsx';
import { apiCall } from './backendConfig.jsx';

const SaveButton = (props) => {

  const autoSave = useRef(true)
  const { experiment, set_experiment } = useContext(ExperimentContext)

  const save = () => {
    apiCall({
      route: "saveExperiment",
      body: { ...experiment, autosave: autoSave.current }
    })
  }

  const explicitSave = () => {
    autoSave.current = false
    save()
    set_experiment(prev => ({ ...prev, version: prev.version + 1 }))
  }

  useEffect(() => { //save on change 
    autoSave.current = true
    save()
  }, [experiment])

  return (
    <button onClick={explicitSave}>Save</button>
  )
}
export default SaveButton
