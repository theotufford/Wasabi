function removeDupes() {
  // remove any element from the bay found both in the bay and the assigned reagents
  const activeReagents = Array.from(document.querySelectorAll('.reagent'))
  activeReagents.forEach((reagent) => {
    const firstInst = document.getElementById(reagent.id) 
    // getElementById returns only the first occurance of the element 
    // if the first occurance of an element by our reagent id is not our selected current loop element it means that we have found a duplicate
    // we can use this to delete the first occurance (which is the one in the reagent bay)
    if (firstInst !== reagent) {
      if (firstInst.parentElement.id === "reagentBay"){
        firstInst.remove()
        reagent.classList.add("confirmed")
      }
    }
  })
}
function getChangeButton(reagent){
  const reagentPumpId = reagent.parentElement.classList.item(0)
  console.log(reagentPumpId)
  const buttonArray = Array.from( document.querySelectorAll('.confirmChange'))
  for (const button of buttonArray){
    if (button.classList.item(0) === reagentPumpId){
      console.log('item')
      return button
    }
  }
}


function changeHandler(reagentObject){
    container = reagentObject.parentElement

    if (reagentObject.classList.contains('toReplace')){
      if (container.id === "reagentBay"){
        reagentObject.remove()
      }
      return;
    }
    else if (container.id === "reagentBay"){
      reagentObject.className = "reagent"
    }
    else {
      reagentObject.classList.add('unconfirmed')
      const button = getChangeButton(reagentObject)
      button.id = reagentObject.innerText
      console.log(button)
      button.classList.remove('hidden')
    }

}


function addReagentEvent(element) {
  element.addEventListener('click', ev => {
    if (ev.target.classList.contains("confirmed")){
      return;
    }
    if (reagentSelected) {
      handleSwap(ev.target)
    } else {
      ev.target.classList.add("selected")
      reagentSelected = ev.target
    }
  })
}


function confirmReagentChange(button){
  const reagent = button.id
  const reagentObject = document.getElementById(reagent)
  const pump = button.classList.item(0)
  backend_call("pumpUpdate", {"pump":pump, "reagent":reagent})
  reagentObject.classList = 'reagent confirmed'
  button.classList.add('hidden')
}

let reagentSelected = false;

function handleSwap(secondSelect) {
  const firstSelect = reagentSelected
  const selects = [
    {
      initialObj:firstSelect,
      obj:firstSelect.cloneNode(1),
      target:secondSelect.parentElement
    },
    {
      initialObj:secondSelect,
      obj:secondSelect.cloneNode(1),
      target:firstSelect.parentElement
    }
  ]
  reagentSelected = false;
  selects.forEach((selectObj) => {
    if(selectObj.initialObj instanceof HTMLButtonElement){ 
    selectObj.target.appendChild(selectObj.obj)
    selectObj.initialObj.remove()
    selectObj.obj.classList.remove('selected')
    changeHandler(selectObj.obj)
    addReagentEvent(selectObj.obj)
    }
    else{
      return;
    }
  })
}
function showfinder() {
  document.getElementById("finder").src = document.getElementById("finder").src;
  document.getElementById("finderContainer").classList.remove("hidden");
}
function hideFinder() {
  hide(document.getElementById("finderContainer"));
}

let dblSpaceWindowOpen = false;
function dblpresstimer_start() {
  if (dblSpaceWindowOpen){
    showfinder();
    return
  }
  dblSpaceWindowOpen = true;
  return new Promise((resolve) => {
    setTimeout(() => {
      dblSpaceWindowOpen = false;
      resolve();
    }, 200);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  removeDupes()
  const activeReagents = Array.from(document.querySelectorAll('.reagent'))
  activeReagents.forEach((reagent) => {
    addReagentEvent(reagent)
  })
  const reagentChangeButtons = Array.from(document.querySelectorAll('.confirmChange'))
  reagentChangeButtons.forEach((button) => {
    button.addEventListener('click', ev => {
      confirmReagentChange(ev.target)
    })
  })
  document.addEventListener("keypress", async (event) => {
    if (event.key === " ") {
      dblpresstimer_start()
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      if (!(globalThis.parent)) {
        hideFinder();
      }
      globalThis.parent.hideFinder();
    }
  });

  const runButton = document.getElementById('runExperiment')

  runButton.addEventListener('click', async () => {
    const response = fetch(window.location.href, {
      method:"post",
      body: "run"
    })
    console.log(await response.text())
  })

  const programmerButton = document.getElementById('programmer')
  programmerButton.addEventListener("click", () => {
    const params = new URLSearchParams(document.location.search);
    const Experiment = {
      'title':params.get('title'),
      'version':params.get('version')
    };
    globalThis.parent.location = `${loadedurls.programmer}?title=${Experiment.title}&version=${Experiment.version}`;
  });
});
