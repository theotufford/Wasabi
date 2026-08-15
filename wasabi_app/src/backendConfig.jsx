// "undefined" means the URL will be computed from the `window.location` object

export const apiCall = async (args) => {
  const method = args?.method || "POST"
  console.log("args: ", args)
  const jsonResponse = await fetch(`api/dataApi/${args?.route}`, {
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
  const jsonResponse = await fetch(`api/control/${args?.route}`, {
    method: method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(args?.body)
  })
    .then(response => (response.json()))
  return (jsonResponse)
}




export const dataStream = new EventSource(`api/control/serial_stream`)


export default apiCall
