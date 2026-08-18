function Well_Cell(props) {
  const wellId = props.id
  const enable_input = props?.enable_input
  const color = props?.color

  if (enable_input === true) {
    return <div><input id={wellId} onInput={props.onInput} /></div>
  }
  else {
    return (
      <div id={wellId} onMouseOver={ev => { ev.preventDefault() }} onClick={props.onClick} className="wellObject">
        <svg version="1.1" viewBox="-50 -50 100 100"
          width="100%" height="100%"
          xmlns="http://www.w3.org/2000/svg">
          <square cx="0" cy="0" r="50" fill={color} />
          <text x="0" y="0" fontSize="30" dominantBaseline="middle" textAnchor="middle" fill="white">{wellId}</text>
        </svg>
      </div>
    )
  }

}

export default Well_Cell
