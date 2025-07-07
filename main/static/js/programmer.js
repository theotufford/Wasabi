function showfinder() {
  document.getElementById("finder").src = document.getElementById("finder").src;
  document.getElementById("plateContainer").classList.add("hidden");
  document.getElementById("finderContainer").classList.remove("hidden");
}
function hideFinder() {
  show(document.getElementById("plateContainer"));
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
  renderPlate();
  const addbutton = document.getElementById("add_instruction");
  const plateSelect = document.getElementById("plateSelector");
  const storeButton = document.getElementById("store_experiment");
  const nameField = document.getElementById("title");

  storeButton.addEventListener("click", () => {
    dump_experiment();
  });
  addbutton.addEventListener("click", () => {
    const newform = new InstructionForm(); // Create instance
    document.getElementById("form_container").appendChild(newform); // Append to DOM
  });
  plateSelect.addEventListener("change", () => {
    renderPlate();
  });
  document.addEventListener("resize", renderPlate());

  if ((Experiment !== "None") && (Experiment !== undefined)) {
    render_experiment(Experiment);
  } else {
    render_experiment("autosave");
  }

  const finderButton = document.getElementById('finderButton')
  const homeButton = document.getElementById('homeButton')
  finderButton.addEventListener("click", showfinder);
  homeButton.addEventListener("click", () => {
    globalThis.parent.location = `${
      loadedurls["home"]
    }?title=${Experiment.title}&version=${Experiment.version}`; // these values are loaded from the url in the header of the file already
  });

  nameField.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
      nameField.blur(); // Remove focus from the input field
    }
  });
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
});

