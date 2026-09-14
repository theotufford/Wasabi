import { useState, useRef, useEffect, useContext } from 'react'
import { AppGlobalContext } from '@src/AppGlobalContext.jsx';
import { apiCall } from '@src/backendConfig.jsx';

const SaveButton = (props) => {

  const autoSave = useRef(true)
  const { experiment, set_experiment } = useContext(AppGlobalContext)

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
    // TODO make sure experiment browser updates? maybe do an event emission system
  }


  // for implicit saveas
  const titleref = useRef(experiment.title)

  useEffect(() => { //autosave on change 
    autoSave.current = true
    save()
  }, [experiment])

  return (
    <button onClick={explicitSave}>Save</button>
  )
}

export default SaveButton
