import { useState, useRef, useEffect, useContext } from 'react'
import { AppGlobalContext } from './AppGlobalContext.jsx'
import apiCall from './backendConfig.jsx'
import { div } from 'motion/react-m'

const BrowserElement = (props) => {
  const { experiment, set_experiment, load_experiment } = useContext(AppGlobalContext)
  const [visible_experiments, set_visible_experiments] = useState([])
  const [search_idling, set_search_idling] = useState(false)
  const search_is_open = useRef(false)

  const select_experiment = (experiment) => {
    load_experiment(experiment.id, experiment.version)
    const dialog_target = document.getElementById("browser")
    dialog_target.close()
  }

  const filter_older_versions = (experimentlist) => {
    if (experimentlist.length == 0) {
      return
    }
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

  const handle_search = (event) => {
    const search_value = event.target.value
    const tempList = []
    set_search_idling(true)
    apiCall({
      route: "search_experiments",
      body: {
        search_value: search_value
      }
    })
      .then(apiResponse => {
        const data = apiResponse.data
        console.log(data)
        data?.forEach((experiment) => {
          const { data, ...db_meta } = experiment
          tempList.push({ ...JSON.parse(data), ...db_meta })
        })
        if (event.target.value != search_value) { return }
        set_search_idling(false)
        set_visible_experiments(filter_older_versions(tempList))
      })
  }

  return (
    <dialog key={props.key} id="browser">
      <ul style={{ listStyleType: 'none' }}>
        {search_idling ?
          <div>
            waiting for database response
          </div> :
          visible_experiments?.length > 0 ?
            visible_experiments?.map(exp => (
              <li key={exp.id} className='searchListItem' onClick={() => select_experiment(exp)}>
                {exp.title}
              </li>
            )) : <div>
              no results found
            </div>}
      </ul>
      <input onChange={handle_search} />
    </dialog>
  )
}
export default BrowserElement
