import { useEffect } from 'react';
import { useRef } from 'react';
import {io} from 'socket.io-client'

const socket = io('http://localhost:5000')

const saveExperiment = async () => {
  fetch("http://localhost:5000/api/saveExperiment")
}

function ApiElement(props){
  const experiment = props.experiment
  useEffect(() => {
  console.log('would call save')
  }, [experiment])
  socket.on('timer', (data) => {
    console.log(data)
  })
}

export default ApiElement





