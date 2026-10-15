import { useState, useRef, useEffect, useContext } from 'react'
import { AppGlobalContext } from './AppGlobalContext.jsx'
import apiCall from './backendConfig.jsx'

const BrowserElement = (props) => {

  const { experiment, set_experiment, load_experiment } = useContext(AppGlobalContext)

  const [visible_experiments, set_visible_experiments] = useState([])

  const filter_older_versions = (experimentlist) => {
    let ids = experimentlist.map(exp => exp.id)
    const unique_ids = [... new Set(ids)]
    const highest_versioned_of_id = []
    unique_ids.forEach(id => {
      const instances = experimentlist.filter(exp => exp.id == id)
      let highest_inst = instances[0]
      instances.forEach(inst => {
        if (inst.version > highest_inst.version) {
          highest_inst = inst
        }
      })
      highest_versioned_of_id.push(highest_inst)
    })
    return highest_versioned_of_id

  }

  const get_experiments = () => {
    const tempList = []
    apiCall({ route: "experiment_dump" })
      .then(apiResponse => apiResponse.data)
      .then(data => data.forEach((experiment) => {
        const {data, ...db_meta} = experiment 
        tempList.push({...JSON.parse(data), ...db_meta})
      }))
      .then(() => {
        console.log("got exp list: ", tempList)
        set_visible_experiments(filter_older_versions(tempList))
      })
  }

  useEffect(() => {
    get_experiments()
  }, [])


  const select_experiment = (experiment) => {
    load_experiment(experiment.id, experiment.version)
    const dialog_target = document.getElementById("browser")
    dialog_target.close()
  }

  const handle_search = (event) => {
    const search_value = event.target.value
  }

  return (
    <dialog key={props.key} id="browser">
      <ul style={{ listStyleType: 'none' }}>
        {visible_experiments.map(exp => (
          <li key={exp.id} className='searchListItem' onClick={() => select_experiment(exp)}> {exp.title} {exp.version} </li>
        ))}
      </ul>
      <input onInput={handle_search} />
    </dialog>
  )
}
export default BrowserElement
