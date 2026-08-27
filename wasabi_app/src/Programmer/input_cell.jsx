function Input_Cell(props) {
  const input_args = { ...props }
  if (props.volume != 0) {
    input_args.defaultValue = props.volume
  } else {
    delete input_args.volume
  }
  return (
  )

}

export default Input_Cell
