const devUrl = "http://localhost:5000" //  TODO CHANGE
// "undefined" means the URL will be computed from the `window.location` object
export const apiCall = async (args) => {
	const method  = args?.method || "POST"
	console.log("args: ",args)
	const jsonResponse = await fetch(`${devUrl}/dataApi/${args?.route}`, {
		method:method,
		headers: { 'Content-Type': 'application/json' },
		body:JSON.stringify(args?.body)
	})
	.then(response => (response.json()))
	return(jsonResponse)
}

export const dataStream = new EventSource(`${devUrl}/serialComs`)


export default apiCall
