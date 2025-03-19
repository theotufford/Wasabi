    document.addEventListener('DOMContentLoaded', function () {
      renderPlate()
      let addbutton = document.getElementById("add_instruction")
      let plateSelect = document.getElementById("plateSelector")
      let storeButton = document.getElementById("store_experiment")
      let finderButton = document.getElementById("finderButton")
      let nameField = document.getElementById('title')

      storeButton.addEventListener("click", function () {
        dump_experiment()
      })
      addbutton.addEventListener("click", function () {
        let newform = new InstructionForm(); // Create instance
        document.getElementById("form_container").appendChild(newform); // Append to DOM
      });
      plateSelect.addEventListener("change", function () {
        renderPlate()
      })
      document.addEventListener('resize', renderPlate())

      if ((Experiment != "None") && (Experiment != undefined)) {
        render_experiment(Experiment)
      } else {
        render_experiment("autosave")
      }

      finderButton.addEventListener('click', function(){
        document.getElementById('finder').src = document.getElementById('finder').src
        document.getElementById('plateContainer').classList.add('hidden') 
        document.getElementById('finderContainer').classList.remove('hidden')
      })
      nameField.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
          nameField.blur(); // Remove focus from the input field
        }
      });
    })