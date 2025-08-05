export function hlwrld(inp) {
    const response = fetch('http://localhost:5000/api/', {
      method:"POST",
      headers:{
        'content-Type': 'application/json',
      },
      body: JSON.stringify({
        function_target:"baseFunction",
        args:inp
      })
    })
    .then((response) => (response.json()))
    .then((json) => console.log('json!: ', json))
  return response 
}
