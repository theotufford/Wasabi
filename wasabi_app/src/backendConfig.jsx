const devUrl = "http://10.0.0.225:5000/" //  TODO CHANGE
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

export const dataStream = new EventSource(`${devUrl}/control`)


export default apiCall
