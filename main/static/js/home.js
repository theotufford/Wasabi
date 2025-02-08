//import other needed modules 
function pumpUpdatejs(updateValue){

  let pump = document.getElementById("selectPump").value

  fetch("/", {
    body: JSON.stringify({
      pump : pump,
      pumpValue: updateValue
    }),
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then((response) => response.json())
  .then((json) => console.log(json));
}