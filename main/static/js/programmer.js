const experiment_data = {};
const render_data = {};
const loadedurls = {};
const svgns = "http://www.w3.org/2000/svg";
let alphabet = "abcdefghijklmnopqrstuvwxyz".split("");
const wellColor = "teal"
// utilities
let colors = [
	"#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
	"#B22222", "#ADFF2F", "#4682B4", "#FF6347", "#9400D3", "#5F9EA0",
	"#FF69B4", "#40E0D0", "#8B0000", "#7CFC00", "#00008B", "#DAA520",
	"#C71585", "#00FA9A", "#FF8C00", "#9932CC", "#2E8B57", "#8B4513",
	"#6A5ACD", "#D2691E", "#556B2F", "#FF00A5"
]; //thanks chatgpt XD
function getRandomColor() {


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

well_color_obj = {}

// ------------- svg well plate rendering -------------
class wellElement extends HTMLElement {
	constructor(row, column, radius){ 
		super();
		this.id = `${toggle_alphanumeric(row)}${column+1}`;
		this.r = radius
		this.x = (column*radius*2)+radius;
		this.y = (row*radius*2)+radius;
		this.color = wellColor
		this.forms = ""
		this.render()
		
	}
	addForm(form){
		this.forms = this.forms + form.id + " "
		if(well_color_obj[this.forms] != undefined){
			this.color = well_color_obj[this.forms]
		}else{
			well_color_obj[this.forms] = getRandomColor()
			this.color = well_color_obj[this.forms]
		}

	}
	render(){
		let svgCanvas = document.getElementById("plateSvgElement")
		this.label = document.createElementNS(svgns, "text")
		let label = this.label
		this.baseCircle = document.createElementNS(svgns, "circle")
		setAttributes(this.baseCircle, {
			"cx": this.x,
			"cy": this.y,
			"r": this.r,
			"fill": this.color,
		})
		svgCanvas.appendChild(this.baseCircle)
		setAttributes(label, {
			"x": this.x, 
			"y": this.y,
			"text-anchor": "middle",
			"class": "wellLabel",
			"dominant-baseline":"middle"
		})

		label.innerHTML = this.id
		svgCanvas.appendChild(this.baseCircle)
		svgCanvas.appendChild(label);
	}
}

customElements.define('well-element', wellElement);
function canvasClear(){
	document.querySelectorAll('well-element').forEach(element => {
		element.remove()
	})
	let svg = document.getElementById("plateSvgElement");
	svg.innerHTML = ""

}
function svgResize(){
	let svg = document.getElementById("plateSvgElement");
    let bbox = svg.getBBox(); // Get bounding box of all elements
	svg.classList.toggle("prePopulationSvgCanvas")
    svg.setAttribute("viewBox", `${bbox.x} ${bbox.y} ${bbox.width} ${bbox.height}`);
}

const ComboColors = {}

function renderPlate(){
	try {
		canvasClear()
	} catch (error) {
		
	}
	let wellContainer = document.getElementById("wellContainer")
	const svgCanvas = document.getElementById("plateSvgElement")
	svgCanvas.classList.toggle("prePopulationSvgCanvas")
	boundingRect = svgCanvas.getBoundingClientRect();
	let selected = document.getElementById("plateSelector").value; 
	let plate = JSON.parse(selected)
	let forms = document.querySelectorAll("instruction-form")
	let radius = 20
	document.querySelector('well-element')
	for (let i = 0; i < plate.y; i++) {
		for (let j = 0; j < plate.x; j++) {
			let well = new wellElement(i, j, radius);
			wellContainer.appendChild(well)
		}
	}
	forms.forEach(form => {form.handle_fromto()})
	document.querySelectorAll('well-element').forEach(well => {
		well.render()
	})

	svgResize()
	console.log("render done")

}
//------------- form interactions -------------
class InstructionForm extends HTMLElement {
	constructor(inputdata) {
		super();
		this.experiment_data = inputdata;
		this.id = "form_" + document.getElementById("form_container").children.length;
	}
	async connectedCallback() {
		this.innerHTML = await this.render_form()
		this.add_listeners()
		this.from = this.querySelector(".from") 
		this.to = this.querySelector(".to")
		this.handle_fromto()
		let colorBlock = this.querySelector("#colorBlock")
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
		this.remove();
		renderPlate(true)
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
				this.addthisform(`${row}${col}`)
			})
		})
	}
	addthisform(wellID){
		let well = document.getElementById(wellID)
		well.addForm(this)
	}


	async method_update(method){
		await backend_call("getMethodForm", {method})
		.then((html) => {
			let container = this.querySelector(".method_container")
			container.innerHTML = ""
			container.innerHTML = html
		});
		

	}
	add_listeners(){

		let selector = this.querySelector(".methodSelect")
		let from  = this.querySelector(".from")
		let to  = this.querySelector(".to")
		let del = this.querySelector("#deleteBtn")
		//let activator = this.querySelector("#activateBtn")

		selector.addEventListener("change", () => this.method_update(selector.value));
		from.addEventListener("change", () => renderPlate());
		to.addEventListener("change", () => renderPlate());
		del.addEventListener('click', () => this.deleteform())
		//activator.addEventListener('click', () => this.activate())
		
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
	let newCombo = new Event("newCombo")
	document.addEventListener
	plateSelect.addEventListener("change", function(){
		renderPlate()
	})
	document.addEventListener('resize', renderPlate())


})
