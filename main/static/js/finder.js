document.addEventListener("DOMContentLoaded", function () {
  renderPlate();
  document.querySelectorAll(".experimentTitle").forEach((title) => {
    title.addEventListener("dblclick", function () {
      selected(title);
    });
  });
  document.querySelectorAll(".versionSelector").forEach((select) => {
    select.addEventListener("change", function () {
      selected(select.parentElement);
    });
  });
  document.getElementById("delete").addEventListener("click", function () {
    const experiment = document.getElementsByClassName("selected")[0];
    const version = experiment.firstElementChild.value;
    if (
      globalThis.confirm(
        `are you sure you want to delete ${experiment.id}_v${version}`,
      )
    ) {
      backend_call("deleteExperiment", {
        "title": experiment.id,
        "version": version,
      });
    }
  });
  document.getElementById("edit").addEventListener("click", function () {
    const experiment = document.getElementsByClassName("selected")[0];
    const version = experiment.firstElementChild.value;
    globalThis.parent.location = `${
      loadedurls["programmer"]
    }?title=${experiment.id}&version=${version}`;
  });
  document.getElementById("run").addEventListener("click", function (params) {
    const experiment = document.getElementsByClassName("selected")[0];
    const version = experiment.firstElementChild.value;
  });
  const search = document.getElementById("search");
  const allTitles = Array.from(document.querySelectorAll(".experimentTitle"));
  let displayed = [];
  search.addEventListener("input", function () {
    if (search.value == "") {
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
