const experiment_data = {};
const render_data = {};
const loadedurls = {};
const svgns = "http://www.w3.org/2000/svg";
let alphabet = "abcdefghijklmnopqrstuvwxyz".split("");
const wellColor = "#ff0ff0"
// utilities
function toggle_alphanumeric(input){
	if (Number.isInteger(input)) {
		return alphabet[input]
	}else{
		return alphabet.indexOf(input);
	}
}
function row(value){ // returns the row of a well
	return toggle_alphanumeric(value[1]);
}
function column(well){ // returns the column of a well
	return toggle_alphanumeric(well[0]);
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



function subtract_set(arr1, arr2) {
	const set2 = new Set(arr2);
	return arr1.filter(item => !set2.has(item));
}
// ------------- svg well plate rendering -------------
class circleBox extends HTMLElement {
	static instances = new WeakSet();
	constructor(row, column, color, radius){ 
		super();
		this.color = color;
		this.row = column;
		this.color = color;
		this.id = `${toggle_alphanumeric(row)}${column}`;
		this.radius = radius
		this.x = (column*radius*2)+radius;
		this.y = (row*radius*2)+radius;
		this.r = radius
		circleBox.instances.add(this);
		console.log(`new circle; x:${this.x} y:${this.y} radius:${this.radius} (column,row):(${column},${row})`)
		this.render()
	}
	render(){
		const svgCanvas = document.getElementById("plateSvgElement")
		this.svgCircle = document.createElementNS(svgns, "circle");
		this.label = document.createElementNS(svgns, "text")
		let svgCircle = this.svgCircle
		let label = this.label
		svgCircle.setAttribute("cx", this.x);
		svgCircle.setAttribute("cy", this.y);
		svgCircle.setAttribute("r", this.r);
		svgCircle.setAttribute("fill", this.color);
		label.setAttribute("x", this.x)
		label.setAttribute("y", this.y)
		label.setAttribute("text-anchor", "middle")

		label.innerHTML = this.id
		svgCanvas.appendChild(svgCircle);
		svgCanvas.appendChild(label);
		
	}
	recolor(){
		this.svgCircle.setAttribute("fill", this.color)
	}
}

customElements.define('circle-box', circleBox);

function canvasClear(){
	const svgCanvas = document.getElementById("plateSvgElement")
	Array.from(svgCanvas.children).forEach(child => {
		svgCanvas.removeChild(child);
	});
}

function renderPlate(boundingRect){
	let wellContainer = document.getElementById("wellContainer")
	canvasClear();
	console.log("rendering plate")
	const svgCanvas = document.getElementById("plateSvgElement")
	if (boundingRect == null) { 
		boundingRect = svgCanvas.getBoundingClientRect;
	}
	selected = document.getElementById("plateSelector").value; 
	plate = JSON.parse(selected)
	canvasRect = svgCanvas.getBoundingClientRect();
	width = canvasRect.height
	console.log(`x:${plate.x} y:${plate.y}, width:${width}`)
	radius = (width/plate.x)/2
	for (let i = 0; i < plate.x; i++) {
		for (let j = 0; j < plate.y; j++) {
			let well = new circleBox(i, j, wellColor, radius);
			wellContainer.appendChild(well)
			well.render();
			svgCanvas.setAttribute("width", `${plate.x*radius}`)
		}
	}
}
//------------- form interactions -------------
class InstructionForm extends HTMLElement {
	constructor(inputdata) {
		super();
		this.experiment_data = inputdata;
		this.from = this.get_form_child("from") 
		this.to = this.get_form_child("to")
		this.id = "form_" + document.getElementById("form_container").children.length;
	}
	async connectedCallback() {
		console.log("added!")
		this.innerHTML = await this.render_form()
		//.then (this.add_listeners())
		//.then (this.handle_fromto())
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
		console.log("deleteform")
		if(this.previousElementSibling() != null){
			this.previousElementSibling().activate();
			this.remove();
		}else if(this.nextElementSibling() != null){
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

	get_form_child(query){
		document.querySelectorAll(query)
			.forEach(element => { // adds change listener to method select child of this form
				console.log(element)
				if (this.contains(element)){
					return element
				}
			})
	}

	handle_fromto() {
		let element = this.from
		let endPoint = this.to
		if (endPoint != null) {
			return
		}
		let diff = {
			'x': (toggle_alphanumeric(element.value[0]) - toggle_alphanumeric(endPoint)),
			'y': (column(element.value) - column(endPoint))
		}
		let direction = { "x": Math.sign(diff.x), "y": Math.sign(diff.y) }
		let columns = Array.from({ length: Math.abs(diff.x) }, (_, i) => i + direction.x)
		let rows = Array.from({ length: Math.abs(diff.y) }, (_, i) => i + direction.y).map(row => toggle_alphanumeric(row))
		columns.forEach(column => {
			rows.forEach(row => {
				highlight_toggle(`${column},${row}`)
			})
		})
	}
	method_update(){
		this.get_values().method 
	}
	add_listeners(){

		let selector = this.get_form_child("#method")
		selector.addEventListener("change", selector.methodUpdate(selector.value));
		
		[this.from,this.to].forEach(element => {
			element.addEventListener("change", this.handle_fromto());
		})

		let del = this.get_form_child("deleteMe")
		del.addEventListener('click', this.deleteform())

		let activator = this.get_form_child("setActive")
		activator.addEventListener('click', this.activate())
		
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
