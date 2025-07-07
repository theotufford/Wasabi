function showfinder() {
  document.getElementById("finder").src = document.getElementById("finder").src;
  document.getElementById("plateContainer").classList.add("hidden");
  document.getElementById("finderContainer").classList.remove("hidden");
}
dblSpaceWindowOpen = false;
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
  const finderButton = document.getElementById("finderButton");
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

  finderButton.addEventListener("click", showfinder);

  nameField.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
      nameField.blur(); // Remove focus from the input field
    }
  });
  document.addEventListener("keypress", async (event) => {
    if (event.key === " ") {
      const timer = dblpresstimer_start()
      console.log(dblSpaceWindowOpen)
    }
  });
});

