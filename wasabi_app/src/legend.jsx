import { useState } from 'react'
import { useEffect } from 'react';
import './legend.css'

const diffBlockDefault = {
	width: "2vw",
	height: "1vh"
}
const keyDefault = {
	display: "flex",
	flexFlow: "column nowrap",
	margin: "2vw",
	justifyContent: "center"
}
function LegendElement(props) {
	const formArray = props.experiment.formArray
	const [legend, setLegend] = useState([<div> empty </div>])
	const updateLegend = () => {
		console.log(props)
		const colorLib = props.colorLib
		const keyArray = Array.from(props.activeKeys.current)
		const formKeySets = keyArray.map((formKeyString) => (new Set(JSON.parse(formKeyString))))
		let keysBySize = []
		formKeySets.forEach((keySet) => {
			const keySize = keySet.size
			if (!keysBySize[keySize]) {
				keysBySize[keySize] = []
			}
			keysBySize[keySize].push(keySet)
		})
		keysBySize = keysBySize.filter(set => set) // remove empty indexes, shortening the list to its order 
		if (keysBySize.length < 1) {
			return
		}
		const minKeySize = keysBySize[0][0].size // grab smallest key size (useful if for all the wells have n contents where n>1)
		const keySets = keysBySize.reverse(); // set order descending in size
		const sizeCount = keySets.length
		const tree = new Map()
		const renderedBranches = []
		const defaultRender = (args) => {
			const diffColor = args.diffColor
			const selfColor = args.selfColor
			const addingSymbol = diffColor ? ['', ''] : ''
			const info = args.info
			const children = args.children ? <div className='children'> {args.children.map((child) => (child?.html))} </div> : ''
			return (
				<div key={selfColor} style={{ ...keyDefault, border: 'solid', borderColor: selfColor }} className='keyContainer'>
					<div className='keyBase'>
						{addingSymbol[0]} <div className="diffColorBlock" style={{ ...diffBlockDefault, backgroundColor: diffColor }} />
						{addingSymbol[1]}{info}
						<div className="selfColorBlock" style={{ backgroundColor: selfColor }} />
					</div>
					{children}
				</div>
			)
		}
		keySets.forEach((layer, layerIndex) => {
			if (layerIndex > sizeCount) {
				console.log('no parents found and len not min size ? basically how did this key get here: ', layer)
				return
			}
			const nextLayer = keySets.length === 1 ? keySets[0] : keySets[layerIndex + 1]
			keyLoop: for (const keySet of layer) {
				const color = colorLib[JSON.stringify([...keySet])]
				const branch = tree.get(keySet)
				if (keySet.size === minKeySize) {
					let singlet_info = '';
					for (const formIndex of [...keySet]) {
						const form = formArray[formIndex]
						singlet_info += `${form?.method} volume of ${form.reagent}\n`
					}
					const renderData = { info: singlet_info, selfColor: color, children: branch?.children }
					const render = defaultRender(renderData)
					tree.set(keySet, {
						html: render,
						children: branch?.children
					})
					renderedBranches.push(render)
					continue
				}
				if (!nextLayer) {
					return
				}

				for (const smallerKey of nextLayer) {
					if (smallerKey.isSubsetOf(keySet)) {

						let info = ''
						let children = [];

						if (branch) {
							children = branch.children
						}

						const diffKeys = keySet.difference(smallerKey)
						const diffColor = colorLib[JSON.stringify([...diffKeys])]

						for (const formIndex of [...diffKeys]) {
							const form = formArray[formIndex]
							info += `${form.method} volume of ${form.reagent}\n`
						}

						const keySetHtml = defaultRender({
							diffColor: diffColor,
							info: info,
							children: children,
							selfColor: color
						})

						tree.set(keySet, {
							html: keySetHtml,
							children: children
						})

						const newBranch = tree.get(keySet)

						let parent = tree.get(smallerKey)
						if (!parent) {
							tree.set(smallerKey, { children: [] })
							parent = tree.get(smallerKey)
						}
						parent.children.push(newBranch)
						continue keyLoop;
					}
				}
				nextLayer.push(keySet)
			}
		})
		return renderedBranches
	}
	useEffect(() => {
		//setLegend([])
		const html = updateLegend()
		if (!html) {
			return
		}
		console.log('updateLegend')
		setLegend(html)
	}, [props.experiment])
	return (
		<div className="legendContainer">
			{legend.map((legendBranch) => (legendBranch))}
		</div>
	)
}


export default LegendElement
