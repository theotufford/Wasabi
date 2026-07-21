import { useState, useRef, useEffect, useContext } from 'react'
import { ExperimentContext } from './experiment_context.jsx';
import { apiCall, set_url_param } from './backendConfig.jsx';
const SaveButton = (props) => {
  const { experiment, set_experiment } = useContext(ExperimentContext)
  const autoSave = useRef(true)
  const save = () => {
    apiCall({
      route: "saveExperiment",
      body: { ...experiment, autosave: autoSave.current }
    }).then(response => {
      if (!autoSave.current) {
        console.log("version: ", experiment.version)
        set_url_param("version", experiment.version)
        set_url_param("title", experiment.title)
      }
    })
  }
  const explicitSave = () => {
    autoSave.current = false
    set_experiment(prev => ({ ...prev, version: prev.version + 1 }))
    save()
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
