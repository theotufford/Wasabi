const experiment_data = {};
const render_data = {};
const loadedurls = {};
const svgns = "http://www.w3.org/2000/svg";
let alphabet = "abcdefghijklmnopqrstuvwxyz".split("");
const wellColor = "teal"
// utilities
function getRandomColor() {
	let colors = [
		"#FF5733", // Red-Orange
		"#33FF57", // Green
		"#3357FF", // Blue
		"#F1C40F", // Yellow
		"#9B59B6", // Purple
		"#E74C3C", // Red
		"#1ABC9C", // Teal
		"#2ECC71", // Emerald
		"#3498DB", // Sky Blue
		"#F39C12"  // Orange
	];

	let picked = colors[Math.floor(Math.random() * colors.length)];
	colors = colors.filter((color) => color != picked)
	return picked 

}
function setAttributes(element, attributes) {
  for (const key in attributes) {
    element.setAttribute(key, attributes[key]);
  }
}
function toggle_alphanumeric(input){
	if (Number.isInteger(input)) {
		return alphabet[input]
	}else{
		return alphabet.indexOf(input);
	}
}
function getRow(well){ // returns the row of a well
	return toggle_alphanumeric(well[0]);
}
function getColumn(well){ // returns the column of a well
	return well.slice(1) - 1 
}
//------------- backend data interactions -------------
function assignUrl(url, key) { //gets dynamic urls from render for use in calls
	loadedurls[key] = url;
}
async function backend_call(function_target, args){   //database call function. call<string>
		let response = await fetch(loadedurls["agent"], {
			method: 'POST', 
			headers: {'Content-Type': 'application/json'},
			body: JSON.stringify({'function_target': function_target, 'args': args})
		});
		return response.text()
}
async function ensureRendered() {
		return new Promise((resolve) => setTimeout(resolve, 0)); // Wait for next event loop tick
	}
function subtract_set(arr1, arr2) {
	const set2 = new Set(arr2);
	return arr1.filter(item => !set2.has(item));
}

// ------------- svg well plate rendering -------------
class circleBox extends HTMLElement {
	static instances = new WeakSet();
	constructor(row, column, color, radius){ 
		super();
		this.baseColor = color;
		this.row = column;
		this.id = `${toggle_alphanumeric(row)}${column+1}`;
		this.radius = radius
		this.x = (column*radius*2)+radius;
		this.y = (row*radius*2)+radius;
		this.r = radius
		this.fills = [{"recallID":"base", "color":color}]
		circleBox.instances.add(this);
		this.render()
	}
	render(){
		this.grad = document.createElementNS(svgns, "linearGradient");
		this.svgCircle = document.createElementNS(svgns, "circle");
		this.label = document.createElementNS(svgns, "text")
		const svgCanvas = document.getElementById("plateSvgElement")
		let grad = this.grad
		let svgCircle = this.svgCircle
		let label = this.label

		grad.setAttribute("id", `g-${this.id}`)	

		setAttributes(svgCircle, {
			"cx": this.x,
			"cy": this.y,
			"r": this.r,
			"fill":`url(#${this.grad.id})`
		})
		setAttributes(label, {
			"x": this.x, 
			"y": this.y,
			"text-anchor": "middle",
			"class": "wellLabel",
			"dominant-baseline":"middle"
		})
		this.Highlight()
		label.innerHTML = this.id
		svgCanvas.appendChild(grad);
		svgCanvas.appendChild(svgCircle); 
		svgCanvas.appendChild(label);
	}

	// code for automatically updating the gradient highlight

	Highlight(){
		let grad = document.getElementById(`g-${this.id}`)
		let per = 100/this.fills.length
		for(let i = 1; i<this.fills.length+1;i++){
			let fill = this.fills[i-1]
			let newStop = document.createElementNS(svgns, "stop")
			setAttributes(newStop, {
				"id": `origin_${fill.recallID}`, 
				"offset": `${per*i}%`, 
				"stop-color": `${fill.color}`
			})
			this.grad.appendChild(newStop)
		}
	}
}

customElements.define('circle-box', circleBox);


function canvasClear(){
	const svgCanvas = document.getElementById("plateSvgElement")
	Array.from(svgCanvas.children).forEach(child => {
		svgCanvas.removeChild(child);
	});
}
function fillReset(){
	const svgCanvas = document.getElementById("plateSvgElement")
	Array.from(svgCanvas.children).forEach(child => {
		if(child instanceof SVGLinearGradientElement){
			svgCanvas.removeChild(child)
		}
	})
}
function svgResize(){
	let svg = document.getElementById("plateSvgElement");
    let bbox = svg.getBBox(); // Get bounding box of all elements
	svg.classList.toggle("prePopulationSvgCanvas")
    svg.setAttribute("viewBox", `${bbox.x} ${bbox.y} ${bbox.width} ${bbox.height}`);
}
function renderPlate(fill){
	let wellContainer = document.getElementById("wellContainer")
	if(fill){fillReset();}else{canvasClear()}
	const svgCanvas = document.getElementById("plateSvgElement")
	svgCanvas.classList.toggle("prePopulationSvgCanvas")
	boundingRect = svgCanvas.getBoundingClientRect();
	let selected = document.getElementById("plateSelector").value; 
	let plate = JSON.parse(selected)
	let width = boundingRect.width
	let radius = 20
	if(!fill){
		for (let i = 0; i < plate.y; i++) {
			for (let j = 0; j < plate.x; j++) {
				let well = new circleBox(i, j, wellColor, radius);
				wellContainer.appendChild(well)
				well.render();
			}
		}
	}else{
		for (let i = 0; i < plate.y; i++) {
			for (let j = 0; j < plate.x; j++) {
				let well = document.getElementById(`${toggle_alphanumeric(i)}${j+1}`)
				well.render();
			}
		}
	}
	svgResize();
}


//------------- form interactions -------------
class InstructionForm extends HTMLElement {
	constructor(inputdata) {
		super();
		this.experiment_data = inputdata;
		this.id = "form_" + document.getElementById("form_container").children.length;
		this.color = getRandomColor()
	}
	async connectedCallback() {
		this.innerHTML = await this.render_form()
		this.add_listeners()
		this.from = this.querySelector(".from") 
		this.to = this.querySelector(".to")
		this.setAttribute("style", `border-color=${this.color}`)
		this.handle_fromto()
	}
	async render_form() {
		try {
			let response = await backend_call("render_form", this.experiment_data);
			this.setAttribute("class", "active");
			return response; // Ensure a return value
		} catch (error) {
			console.error("Error rendering form:", error);
			return undefined; // Explicitly return undefined in case of failure
		}


	}
	activate(){  // sets the active form to this form
		let active_form = document.getElementsByClassName("active_form")[0]
		if (active_form != undefined){ 
			active_form.classList.remove("active_form")
		}
		this.classList.add("active_form")
	}
	deleteform(){
		if(this.previousElementSibling()){
			this.previousElementSibling().activate();
			this.remove();
		}else if(this.nextElementSibling()){
			this.nextElementSibling().activate();
			this.remove();
		}else{
			this.remove();
		}
	}
	
	get_values(){
		let info_containers = document.getElementsByClassName("experiment_info");
		let values = {};
		info_containers.forEach(info_container => {
			dump[info_container.id] = info_container.value;
		});
		return values
	}

	dump_to_session(){
		dump = {[this.id]:[this.get_values()]}
		backend_call("dump_to_session", dump);
	}
	graphicDisplay(circID) {
		let circEl = document.getElementById(circID)
		circEl.fills.push({ "recallID": this.id, "color": this.color})
	}

	handle_fromto() {
		let fromIn = this.querySelector(".from").value
		let toIn = this.querySelector(".to").value
		let from = {}
		let to  = {}

		if(!fromIn){return undefined}
		if(!toIn){return undefined}

		// make sure to > from 

		if(getColumn(fromIn) > getColumn(toIn)) {
			from['x'] = getColumn(toIn)
			to['x'] = getColumn(fromIn)
		}else{
			from['x'] = getColumn(fromIn)
			to['x'] = getColumn(toIn)
		}

		if(getRow(fromIn) > getRow(toIn)) {
			from['y'] = getRow(toIn)
			to['y'] = getRow(fromIn)
		}else{
			from['y'] = getRow(fromIn)
			to['y'] = getRow(toIn)
		}




		let deltaX = to.x - from.x
		let deltaY = to.y - from.y
		let colArray = []
		let rowArray = (alphabet.slice(from.y,to.y+1))

		for(let i = from.x; i < to.x+1; i++ ){
			colArray.push(i+1)
		}

		rowArray.forEach(row => {
			colArray.forEach(col => {
				this.graphicDisplay(`${row}${col}`)
			})
		})
		renderPlate(true)

	}
	method_update(){
		this.get_values().method 
	}
	add_listeners(){

		let selector = this.querySelector("#method_container")
		let from  = this.querySelector(".from")
		let to  = this.querySelector(".to")
		let del = this.querySelector("#deleteBtn")
		let activator = this.querySelector("#activateBtn")

		selector.addEventListener("change", () => this.methodUpdate(selector.value));
		from.addEventListener("change", () => this.handle_fromto());
		to.addEventListener("change", () => this.handle_fromto());
		del.addEventListener('click', () => this.deleteform())
		activator.addEventListener('click', () => this.activate())
		
	}
}

customElements.define('instruction-form', InstructionForm);

function render_experiment(arg) {
    backend_call("get_experiment", arg)
        .then((response) => {
            response.forms.forEach(form => {
                let newform = new InstructionForm(form); // Create instance
                document.getElementById("form_container").appendChild(newform); // Append to DOM
            });
        });
}

document.addEventListener('DOMContentLoaded', function(){
	renderPlate()
	let addbutton = document.getElementById("add_instruction")
	let plateSelect = this.getElementById("plateSelector")
	addbutton.addEventListener("click", function(){
		let newform = new InstructionForm("empty"); // Create instance
		document.getElementById("form_container").appendChild(newform); // Append to DOM
	});
	document.addEventListener('resize', renderPlate())


})
