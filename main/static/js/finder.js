document.addEventListener("DOMContentLoaded", () => {
  renderPlate();
  document.querySelectorAll(".experimentTitle").forEach((title) => {
    title.addEventListener("dblclick",  () => {
      selected(title);
    });
  });
  document.querySelectorAll(".versionSelector").forEach((select) => {
    select.addEventListener("change",  () => {
      selected(select.parentElement);
    });
  });
async function selected(title) {
  const experiment = title.id;
  const version = document.getElementById(`${experiment}_versionSelect`).value;
  const colors = staticColorLibrary;
  const shorthandContainer = document.getElementById("shorthandBlock");
  const forms = render_experiment({ "title": experiment, "version": version });
  document.querySelectorAll(".experimentTitle").forEach((title) => {
    title.classList.remove("selected");
  });
  console.log(experiment, "\nv", version);
  title.classList.add("selected");
  forms.forEach((form) => {
    form = response[form];
    console.log(form["reagent"], form["method"], "\n");
  });
}

function show(obj) {
  obj.classList.remove("hidden");
}
function hide(obj) {
  obj.classList.add("hidden");
}
function visToggle(obj) {
  obj.classList.toggle("hidden");
}

function limitFinderDisplay() {
  const experiments = Array.from(document.querySelectorAll(".listedTitle"));
  let i = 0;
  experiments.forEach((experiment) => {
    if (experiment.classList.contains("hidden")) {
      i = i + 1;
    } else {
      show(experiment);
      if (i > 20) {
        hide(experiment);
      }
      i = i + 1;
    }
  });
}

function nextPage() {
  const titles = Array.from(document.querySelectorAll(".listedTitle"));
  const search = document.getElementById("search");
  titles.forEach((title) => {
    if (!(title.id.toUpperCase().includes(search.value.toUpperCase()))) {
      console.log("ignored");
    } else {
      visToggle(title);
    }
  });
}
//  document.getElementById("delete").addEventListener("click",  () => {
//    const experiment = document.getElementsByClassName("selected")[0];
//    const version = experiment.firstElementChild.value;
//    if (
//      globalThis.confirm(
//        `are you sure you want to delete ${experiment.id}_v${version}`,
//      )
//    ) {
//      backend_call("deleteExperiment", {
//        "title": experiment.id,
//        "version": version,
//      });
//    }
//  });
  document.getElementById("edit").addEventListener("click",  () => {
    const experiment = document.getElementsByClassName("selected")[0];
    const version = experiment.firstElementChild.value;
    globalThis.parent.location = `${
      loadedurls["programmer"]
    }?title=${experiment.id}&version=${version}`;
  });
  document.getElementById("run").addEventListener("click",  () => {
    const experiment = document.getElementsByClassName("selected")[0];
    const version = experiment.firstElementChild.value;
    globalThis.parent.location = `${
      loadedurls["home"]
    }?title=${experiment.id}&version=${version}`;
  });
  const search = document.getElementById("search");
  const allTitles = Array.from(document.querySelectorAll(".experimentTitle"));
  let displayed = [];
  search.addEventListener("input",  () => {
    if (search.value === "") {
      allTitles.forEach((title) => show(title));
    } else {
      allTitles.forEach((title) => hide(title));
    }
    displayed = allTitles.filter((title) =>
      title.id.toUpperCase().includes(search.value.toUpperCase())
    );
    displayed.forEach((title) => {
      show(title);
    });
    limitFinderDisplay();
  });
  search.focus();
  limitFinderDisplay();
});
