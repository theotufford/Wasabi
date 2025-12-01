import { useState, useRef, useEffect } from 'react'
import  apiCall from './backendConfig.jsx'

const getTitles = (set_titleList) => {
	let tempList = []
	apiCall({ route: "dbDump" })
		.then(apiResponse => apiResponse.data)
		.then()
		.then(data => data.forEach((form) => {
			const title = form.title
			if (tempList.includes(title)) return
			tempList = [...tempList, title]
		}))
		.then(() => set_titleList([...tempList]))
}
const deletePrompt = (title) => {
	const conf = confirm(("are you sure you want to delete ", title))
	if (conf) {
		//emit("delete_experiment", title)
	}
}
//----------------------------------------- individual list item element
const Exp_li = (props) => {
	const title = props.title
	const search = props.searchValue
	const [visible, setVis] = useState(true)

	const run = () => {
		props.setEndpoint("controller")
		props.enableRedirect.current = true
		props.selectTitle(title)
	}
	const edit = () => {
		props.setEndpoint("editor")
		props.enableRedirect.current = true
		props.selectTitle(title)
	}

	useEffect(() => {
		if (search == "*") return
		const simplifiedTitle = title.toUpperCase()
		const simplifiedSearch = search.toUpperCase()

		if (!simplifiedTitle.includes(simplifiedSearch)) {
			setVis(false)
		} else {
			setVis(true)
		}
	}, [title, search])

	return (
		<li style={{ visibility: visible ? 'visible' : 'hidden', }}>
			<button class="selectButton" onClick={edit}>edit</button>
			<button class="selectButton" onClick={run}>run</button>
			{title}
		</li>
	)
}
//----------------------------------------- list element
const ListElement = (props) => {
	const [titleList, set_titleList] = useState(["loading"])
	useEffect(() => {
		getTitles(set_titleList)
	}, [])
	return (
		<ul style={{ listStyleType: 'none' }}>
			{titleList.map(title => (
				<Exp_li
					key={title}
					title={title}
					{...props}
				/>
			))}
		</ul>
	)
}
//----------------------------------------- search bar

const SearchElement = (props) => {
	const search = (event) => {
		const searchValue = event.target.value
		props.set_search(searchValue)
	}
	return (<input onInput={search} />)
}
//----------------------------------------- aggregate browser element 
const BrowserElement = (props) => {
	const [searchValue, set_searchValue] = useState("*")
	const [selectedTitle, set_selectedTitle] = useState("*")
	const experiment = props.experiment
	const setExperiment = props.setExperiment
	const initialLoad = useRef(false)
	const [redirectTarget, setredirectTarget] = useState()
	useEffect(() => {

		if (!initialLoad.current) {
			console.log("escaped autoredirect") // i dont know why this happens and this is a sloppy fix
			return
		}

		console.log('succesful redirect call')

		apiCall({
			route: "fetchExperiment",
			body: {
				title: selectedTitle,
			}
		})
			.then(response => JSON.parse(response.data))
			.then(data => {
				setExperiment(data)
				console.log('set experiment to: ', data)
			})
			.then(() => {
			if (redirectTarget === "editor"){
					props.goToEditor()
				}
			if (redirectTarget === "controller"){
					props.goToController()
				}
			})
	}, [selectedTitle, setExperiment])
	return (
		<div>
			<button onClick={props.goToEditor}>new</button>
			<ListElement
				enableRedirect={initialLoad}
				searchValue={searchValue}
				selected={selectedTitle}
				selectTitle={set_selectedTitle}
				setEndpoint={setredirectTarget}
			/>
			<SearchElement set_search={set_searchValue} />
		</div>
	)
}
export default BrowserElement
