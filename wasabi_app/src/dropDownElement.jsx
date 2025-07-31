import React from 'react'
import Select from 'react-select'
import Creatable from 'react-select/creatable';

function DdSelect() {
const options = [
  { value: 'chocolate', label: 'Chocolate' },
  { value: 'strawberry', label: 'Strawberry' },
  { value: 'vanilla', label: 'Vanilla' }
]

const MyComponent = (
  <div>
  hi
  <Select options={options} />
  </div>
)

  return (MyComponent)
}
export default DdSelect
