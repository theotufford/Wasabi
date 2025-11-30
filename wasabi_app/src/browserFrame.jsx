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
	const search = props.search
	const [visible, setVis] = useState(true)
	const select = () => {
		props.explicitRedir.current = true
		props.set_select(title)
		console.log('set selected')
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
			<button class="selectButton" onClick={select}>o</button>
			{title}
		</li>
	)
}
//----------------------------------------- list element
const ListElement = (props) => {
	const [titleList, set_titleList] = useState(["loading"])
	const search = props.searchValue
	const set_select = props.set_select
	useEffect(() => {
		getTitles(set_titleList)
	}, [])
	return (
		<ul style={{ listStyleType: 'none' }}>
			{titleList.map(title => (
				<Exp_li
					key={title}
					title={title}
					set_select={set_select}
					search={search}
					explicitRedir={props.explicitRedir}
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
	useEffect(() => {
		if (!initialLoad.current) {
			console.log("escaped autoredirect")
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
			.then(() => props.goToEditor())
	}, [selectedTitle, setExperiment])
	return (
		<div>
			<button onClick={props.goToEditor}>new</button>
			<ListElement
				explicitRedir={initialLoad}
				searchValue={searchValue}
				selected={selectedTitle}
				set_select={set_selectedTitle}
			/>
			<SearchElement set_search={set_searchValue} />
		</div>
	)
}
export default BrowserElement
