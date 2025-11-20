import { io } from 'socket.io-client';

const devUrl = "http://localhost:5000" //  TODO CHANGE

// "undefined" means the URL will be computed from the `window.location` object
const URL = process.env.NODE_ENV === 'production' ? undefined : devUrl;
export const socket = io(URL);

export async function apiCall(args) {
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
