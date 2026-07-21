const devUrl = "http://10.136.220.142:5000" //  TODO CHANGE
// "undefined" means the URL will be computed from the `window.location` object

export const apiCall = async (args) => {
  const method = args?.method || "POST"
  console.log("args: ", args)
  const jsonResponse = await fetch(`${devUrl}/dataApi/${args?.route}`, {
    method: method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(args?.body)
  })
    .then(response => (response.json()))
  return (jsonResponse)
}

export const control_call = async (args) => {
  const method = args?.method || "POST"
  console.log("args: ", args)
  const jsonResponse = await fetch(`${devUrl}/control/${args?.route}`, {
    method: method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(args?.body)
  })
    .then(response => (response.json()))
  return (jsonResponse)
}

export const get_url_param = (param) => {
  const searchParams = new URLSearchParams(window.location.search);
  const value = searchParams.get(param)
  return value
}

export const set_url_param = (name, value) => {
  const url = new URL(window.location);
  url.searchParams.set(name, value)
  window.history.pushState({}, "", url)
}

export const get_url_experiment = async () => {
  const title = get_url_param("title")
  const version = get_url_param("version")
  let out_data
  if (title == null || version == null) {
    return false
  }
  await apiCall({
    route: "fetchExperiment",
    body: {
      title: title,
      version: version
    }
  })
    .then(parsed_response => {
      if (parsed_response?.failure == true) {
        return false
      }
      console.log("returning: ", parsed_response)
      out_data = parsed_response
    })
  return out_data
}

export const dataStream = new EventSource(`${devUrl}/control`)


export default apiCall
