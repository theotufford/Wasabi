const experiment_data = {};
const render_data = {};
const loadedurls = {};
const svgns = "http://www.w3.org/2000/svg";
let alphabet = "abcdefghijklmnopqrstuvwxyz".split("");
const wellColor = "teal";
// utilities
const staticColorLibrary = [
  "#FF0000",
  "#00FF00",
  "#0000FF",
  "#FFFF00",
  "#FF00FF",
  "#00FFFF",
  "#B22222",
  "#ADFF2F",
  "#4682B4",
  "#FF6347",
  "#9400D3",
  "#5F9EA0",
  "#FF69B4",
  "#40E0D0",
  "#8B0000",
  "#7CFC00",
  "#00008B",
  "#DAA520",
  "#C71585",
  "#00FA9A",
  "#FF8C00",
  "#9932CC",
  "#2E8B57",
  "#8B4513",
  "#6A5ACD",
  "#D2691E",
  "#556B2F",
  "#FF00A5",
]; //thanks chatgpt XD
const colors = staticColorLibrary;
function getColor() {
  picked = colors.pop();
  return picked;
}

function show(object) {
  object.classList.remove('hidden')
}

function hide(object) {
  object.classList.add('hidden')
}

function setAttributes(element, attributes) {
  for (const key in attributes) {
    element.setAttribute(key, attributes[key]);
  }
}
function toggle_alphanumeric(input) {
  if (Number.isInteger(input)) {
    return alphabet[input];
  } else {
    return alphabet.indexOf(input);
  }
}
function getRow(well) { // returns the row of a well
  return toggle_alphanumeric(well[0]);
}
function getColumn(well) { // returns the column of a well
  return well.slice(1) - 1;
}
//------------- backend data interactions -------------
function assignUrl(url, key) { //gets dynamic urls from render for use in calls
  loadedurls[key] = url;
}
async function backend_call(function_target, args) { //database call function. call<string>
  const response = await fetch(loadedurls.agent, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ "function_target": function_target, "args": args }),
  });
  return response.text();
}
async function ensureRendered() {
  return new Promise((resolve) => setTimeout(resolve, 0)); // Wait for next event loop tick
}
function subtract_set(arr1, arr2) {
  const set2 = new Set(arr2);
  return arr1.filter((item) => !set2.has(item));
}

well_color_obj = {};

// ------------- svg well plate rendering -------------
class wellElement extends HTMLElement {
  constructor(row, column, radius) {
    super();
    this.id = `${toggle_alphanumeric(row)}${column + 1}`;
    this.r = radius;
    this.x = (column * radius * 2) + radius;
    this.y = (row * radius * 2) + radius;
    this.color = wellColor;
    this.forms = "";
    this.render();
  }
  addForm(form) {
    this.forms += `${form.id},`;
    if (well_color_obj[this.forms] !== undefined) {
      this.color = well_color_obj[this.forms];
    } else {
      well_color_obj[this.forms] = getColor();
      this.color = well_color_obj[this.forms];
    }
  }
  render() {
    let svgCanvas = document.getElementById("plateSvgElement");
    this.label = document.createElementNS(svgns, "text");
    let label = this.label;
    this.baseCircle = document.createElementNS(svgns, "circle");
    setAttributes(this.baseCircle, {
      "cx": this.x,
      "cy": this.y,
      "r": this.r,
      "fill": this.color,
    });
    svgCanvas.appendChild(this.baseCircle);
    setAttributes(label, {
      "x": this.x,
      "y": this.y,
      "text-anchor": "middle",
      "class": "wellLabel",
      "dominant-baseline": "middle",
    });

    label.innerHTML = this.id;
    svgCanvas.appendChild(this.baseCircle);
    svgCanvas.appendChild(label);
  }
}

customElements.define("well-element", wellElement);
function canvasClear() {
  document.querySelectorAll("well-element").forEach((element) => {
    element.remove();
  });
  let svg = document.getElementById("plateSvgElement");
  svg.innerHTML = "";
}
function svgResize() {
  let svg = document.getElementById("plateSvgElement");
  let bbox = svg.getBBox(); // Get bounding box of all elements
  svg.classList.remove("prePopulationSvgCanvas");
  svg.setAttribute(
    "viewBox",
    `${bbox.x} ${bbox.y} ${bbox.width} ${bbox.height}`,
  );
}

function renderPlate() {
  try {
    canvasClear();
  } catch (error) {
  }
  let wellContainer = document.getElementById("wellContainer");
  const svgCanvas = document.getElementById("plateSvgElement");
  //svgCanvas.classList.toggle("prePopulationSvgCanvas")
  boundingRect = svgCanvas.getBoundingClientRect();
  const selected = document.getElementById("plateSelector").value;
  let plate = JSON.parse(selected);
  let forms = document.querySelectorAll("instruction-form");
  let radius = 20;
  document.querySelector("well-element");
  for (let i = 0; i < plate.y; i++) {
    for (let j = 0; j < plate.x; j++) {
      let well = new wellElement(i, j, radius);
      wellContainer.appendChild(well);
    }
  }

  forms.forEach((form) => {
    form.handle_fromto();
  });
  document.querySelectorAll("well-element").forEach((well) => {
    well.render();
  });

  svgResize();
}
//------------- form interactions -------------
class InstructionForm extends HTMLElement {
  constructor(inputdata) {
    super();
    this.experiment_data = inputdata;
    this.id = "form_" +
      document.getElementById("form_container").children.length;
  }
  async connectedCallback() {
    this.innerHTML = await this.render_form();
    this.add_listeners();
    this.method_update();
    renderPlate();
    updateLegend();
  }
  async render_form() {
    try {
      const response = await backend_call("render_form", this.experiment_data);
      return response; // Ensure a return value
    } catch (error) {
      console.error("Error rendering form:", error);
      return undefined; // Explicitly return undefined in case of failure
    }
  }
  deleteform() {
    this.remove();
    renderPlate(true);
  }
  get_values() {
    const info_containers = document.getElementsByClassName("experiment_info");
    const values = {};
    Array.from(info_containers).forEach((info_container) => {
      if (this.contains(info_container)) {
        let value = info_container.value;
        if (!(isNaN(value))) {
          value = parseFloat(value);
        }
        values[info_container.id] = value
      }
    });
    return values;
  }

  handle_fromto(obj_from, obj_to) {
    let fromIn = obj_from;
    let toIn = obj_to;

    if (!obj_from) {
      fromIn = this.querySelector(".from").value;
    }
    if (!obj_to) {
      toIn = this.querySelector(".to").value;
    }

    let from = {};
    let to = {};

    if (!fromIn) return undefined;
    if (!toIn) return undefined;

    // fix from-to order so (from<to) (commutativity: [a1:b1].output = [b1:a1].output)

    if (getColumn(fromIn) > getColumn(toIn)) {
      from.x = getColumn(toIn);
      to.x = getColumn(fromIn);
    } else {
      from.x = getColumn(fromIn);
      to.x = getColumn(toIn);
    }

    if (getRow(fromIn) > getRow(toIn)) {
      from.y = getRow(toIn);
      to.y = getRow(fromIn);
    } else {
      from.y = getRow(fromIn);
      to.y = getRow(toIn);
    }

    const colArray = [];
    const rowArray = alphabet.slice(from.y, to.y + 1);

    for (let i = from.x; i < to.x + 1; i++) {
      colArray.push(i + 1);
    }
    rowArray.forEach((row) => {
      colArray.forEach((col) => {
        this.addthisform(`${row}${col}`);
      });
    });
  }

  addthisform(wellID) { // idk why but splitting this helps javascript not do some sort of weird async error
    const well = document.getElementById(wellID);
    well.addForm(this);
  }

  async method_update() {
    const method = this.querySelector(".methodSelect").value;
    await backend_call("getMethodForm", {
      "method": method,
      "renderData": this.experiment_data,
    })
      .then((html) => {
        const container = this.querySelector(".method_container");
        container.innerHTML = "";
        container.innerHTML = html;
      });
  }
  reagentButtonConfig() {
    const buttons = this.querySelectorAll(".reagentButton");
    const input = this.querySelector(".reagentInput");
    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        input.value = button.id;
        this.handleSearch();
      });
    });
  }


  handleSearch() {
    console.log("handling search");
    const buttons = this.querySelectorAll(".reagentButton");
    const input = this.querySelector(".reagentInput");
    const logbutton = this.querySelector("#logReagentButton");
    show(logbutton);
    buttons.forEach((button) => {
      if (button.id.toUpperCase() == input.value.toUpperCase()) {
        hide(logbutton);
      }
      if (document.activeElement != input) {
        hide(button);
      } else if (button.id.toUpperCase().includes(input.value.toUpperCase())) {
        show(button);
      } else {
        hide(button);
      }
    });
  }
  reagentLibUpdate() {
    const logReagentButton = this.querySelector("#logReagentButton");
    const reagentInput = this.querySelector("#reagent");
    this.handleSearch();
    hide(logReagentButton);
    // data formatting is weird here because the lib update function
    // is designed to recursively auto input all of the reagents in
    // a given experiment
    const data = { "form": { "reagent": reagentInput.value } }; // "form" key acts as a processing tag
    backend_call("reagentLibUpdate", data);
  }
  add_listeners() {
    const selector = this.querySelector(".methodSelect");
    const from = this.querySelector(".from");
    const to = this.querySelector(".to");
    const del = this.querySelector("#deleteBtn");
    const reagentInput = this.querySelector("#reagent");
    const logReagentButton = this.querySelector("#logReagentButton");
    this.reagentButtonConfig();
    selector.addEventListener("change", () => this.method_update());
    from.addEventListener("change", () => renderPlate());
    to.addEventListener("change", () => renderPlate());
    del.addEventListener("click", () => this.deleteform());
    reagentInput.addEventListener("input", () => this.handleSearch());
    //  reagentInput.addEventListener("blur", () => this.handleSearch());
    logReagentButton.addEventListener("click", () => this.reagentLibUpdate());
  }
}

customElements.define("instruction-form", InstructionForm);

function dump_experiment(arg) {
  const forms = document.querySelectorAll("instruction-form");
  const dump = {};
  if (arg == "auto") {
    dump.autosave = true;
  }
  forms.forEach((form) => {
    dump[form.id] = form.get_values();
  });
  dump.title = document.getElementById("title").value;
  dump.dimensions = JSON.parse(document.getElementById("plateSelector").value)
  backend_call("dump", dump);
}

function updateLegend() {
  const legendContainer = document.getElementById('color_legend')
  const progenitorLegendObject = legendContainer.querySelector('#template')
  if (legendContainer.childElementCount > 1) {
    legendContainer.childNodes.forEach((child) => {
      if (child.id !== "template") {
        child.remove()
      }
    })
  }
  wells = Array.from(document.querySelectorAll('well-element'))
  active_colors = wells.map((well) => { return well.color })
  const unique_active_colors = [...new Set(active_colors)]
  const formComboArray = Object.keys(well_color_obj)
  const activeColorComboLegend = formComboArray.map((combo) => {
    if (unique_active_colors.includes(well_color_obj[combo])) {
      return {
        color:well_color_obj[combo],
        formIds:combo.split(",").filter((formId) => !!formId)
      }
    }
  }).filter((element) => !!element)

  const reagent_method_color_legend = []
  const allForms = Array.from( document.querySelectorAll('instruction-form'));
  const allFormIds = allForms.map((form) => { return (form.id) })
  let ubiquitousForms = new Set(allFormIds)

  activeColorComboLegend.forEach(legendObject => {
    const idSet = new Set(legendObject.formIds)
    ubiquitousForms = ubiquitousForms.intersection(idSet)
  });

  if (ubiquitousForms.size > 0) {
    activeColorComboLegend.unshift({
      color:'transparent',
      formIds:[...ubiquitousForms],
      isUbiqSet:true
    })
  }

  activeColorComboLegend.forEach((legendObject) => {

    if (!legendObject.isUbiqSet) {
      legendObject.formIds = legendObject.formIds.filter((formId) => !ubiquitousForms.has(formId) )
    }

    const color = legendObject.color
    const legendEntry = {
      "color":color,
      "info":''
    }


    legendObject.formIds.forEach((formId) => {
      const form = document.getElementById(formId)
      const values = form.get_values()
      legendEntry.info += `${values.method} volume of ${values.reagent}\n`;
    })
    reagent_method_color_legend.push(legendEntry)
  })


  reagent_method_color_legend.forEach((legendEntry) => {
    const copyChildren = true
    const newLegendElement = progenitorLegendObject.cloneNode(copyChildren)
    newLegendElement.id = "clone" 
    newLegendElement.classList.remove('hidden')
    newLegendElement.style.backgroundColor = legendEntry.color
    newLegendElement.innerText = legendEntry.info
    legendContainer.appendChild(newLegendElement)
  })
}

function render_experiment(selector) {
  const form_container = document.getElementById("form_container"); //get the form container
  form_container.innerHTML = ""; // clear it
  let forms = [];
  backend_call("getExperiment", selector) // get the backend to return the data of the forms of the instruction
    .then((response) => {
      console.log('getting experiment')
      response = JSON.parse(response);
      if (response.title !== undefined) {
        document.getElementById("title").value = response["title"];
      }
      if (response.dimensions !== undefined) {
        document.getElementById("plateSelector").value = JSON.stringify(response["dimensions"]);
      }

      forms = Object.keys(response).filter((key) =>
        key.substring(0, 5) === "form_" // filter everything that isnt a form
      );

      forms.forEach((form) => {
        const newform = new InstructionForm(response[form]); // Create instance
        form_container.appendChild(newform); // Append to DOM
      });

      renderPlate();

    });
  return forms;
}
