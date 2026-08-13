import { useState, useRef, useEffect, useContext } from 'react'
import { ExperimentContext } from './experiment_context.jsx'
import apiCall from './backendConfig.jsx'
import { set_url_param, get_url_experiment, get_url_param } from './backendConfig.jsx'

const BrowserElement = (props) => {

  const { experiment, set_experiment } = useContext(ExperimentContext)

  const [all_experiments, set_all_experiments] = useState([])
  const [visible_experiments, set_visible_experiments] = useState([])

  const filter_older_versions = (experimentlist) => {
    let titles = experimentlist.map(exp => exp.title)
    const unique_titles = [... new Set(titles)]
    const highest_versioned_of_name = []
    unique_titles.forEach(title => {
      const instances = experimentlist.filter(exp => exp.title == title)
      let highest_inst = instances[0]
      instances.forEach(inst => {
        if (inst.version > highest_inst.version) {
          highest_inst = inst
        }
      })
      highest_versioned_of_name.push(highest_inst)
    })
    console.log(highest_versioned_of_name)
    return highest_versioned_of_name

  }

  const get_experiments = () => {
    const tempList = []
    apiCall({ route: "experiment_dump" })
      .then(apiResponse => apiResponse.data)
      .then(data => data.forEach((experiment) => {
        tempList.push(experiment)
      }))
      .then(() => {
        set_all_experiments(tempList)
        set_visible_experiments(filter_older_versions(tempList))
      })
  }

  useEffect(() => {
    get_experiments()
  }, [])


  const select_experiment = (experiment) => {
    set_url_param("title", experiment.title)
    set_url_param("version", experiment.version)
    get_url_experiment().then((found_experiment) => {
      if (found_experiment == false || found_experiment == undefined) {
        return
      }
      set_experiment(found_experiment)
    })
    const dialog_target = document.getElementById("browser")
    dialog_target.close()
  }

  const handle_search = (event) => {
    const search_value = event.target.value
  }

  return (
    <dialog id="browser">
      <ul style={{ listStyleType: 'none' }}>
        {visible_experiments.map(exp => (
          <li key={exp.title} className='searchListItem' onClick={() => select_experiment(exp)}> {exp.title} {exp.version} </li>
        ))}
      </ul>
      <input onInput={handle_search} />
    </dialog>
  )
}
export default BrowserElement
