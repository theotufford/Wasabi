function showfinder() {
  document.getElementById("finder").src = document.getElementById("finder").src;
  document.getElementById("plateContainer").classList.add("hidden");
  document.getElementById("finderContainer").classList.remove("hidden");
}
function dblpresstimer_start() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve();
    }, 100);
  });
}
document.addEventListener("DOMContentLoaded", function () {
  renderPlate();
  const addbutton = document.getElementById("add_instruction");
  const plateSelect = document.getElementById("plateSelector");
  const storeButton = document.getElementById("store_experiment");
  const finderButton = document.getElementById("finderButton");
  const nameField = document.getElementById("title");

  storeButton.addEventListener("click", function () {
    dump_experiment();
  });
  addbutton.addEventListener("click", function () {
    const newform = new InstructionForm(); // Create instance
    document.getElementById("form_container").appendChild(newform); // Append to DOM
  });
  plateSelect.addEventListener("change", function () {
    renderPlate();
  });
  document.addEventListener("resize", renderPlate());

  if ((Experiment != "None") && (Experiment != undefined)) {
    render_experiment(Experiment);
  } else {
    render_experiment("autosave");
  }

  finderButton.addEventListener("click", showfinder);

  nameField.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      nameField.blur(); // Remove focus from the input field
    }
  });
  document.addEventListener("keypress", async function (event) {
    if (event.key === " ") {
      console.log("hi");
      if (!(globalThis.dblpresstimer)) {
        globalThis.dblpresstimer = true;
        await dblpresstimer_start()
          .then(globalThis.dblpresstimer = false);
      } else {
        showfinder();
        globalThis.dblpresstimer = false;
      }
    }
  });
});

