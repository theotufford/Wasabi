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


export function modify_reagent(name, metadata) {
  apiCall({
    route: "modify_reagent",
    body: {
      name: name,
      metadata: metadata
    }
  })
}
export function delete_reagent(name) {
  apiCall({
    route: "add_reagent",
    body: {
      name: name
    }
  })
}
export function add_new_reagent(name, metadata = {}) {
  console.log("adding new reagent? ", name, metadata)
  if (name === null) {return}
  apiCall({
    route: "add_reagent",
    body: {
      name: name,
      metadata: metadata
    }
  })
}


export const dataStream = new EventSource(`api/control/serial_stream`)


export default apiCall
