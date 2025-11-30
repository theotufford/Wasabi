function WellElement(props) {
  const wellId = props.id
  const color = props.color
  return (
    <div className = "wellObject">
    <svg version="1.1" viewBox = "-50 -50 100 100"
    width="100%" height="100%"
    xmlns="http://www.w3.org/2000/svg">
    <circle cx="0" cy="0" r="50" fill={color} />
    <text x="0" y="0" fontSize="30" dominantBaseline = "middle" textAnchor="middle" fill="white">{wellId}</text>
    </svg>
    </div>
  )
}
export default WellElement


