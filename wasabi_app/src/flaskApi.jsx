import { useEffect } from 'react';
import { useRef } from 'react';
import {io} from 'socket.io-client'

const backendUrl = 'http://localhost:5000'
const socket = io(backendUrl)


function ApiElement(props){
  const experiment = props.experiment

  useEffect(() => {
   socket.emit('dumpExperimentToSession', experiment)
  }, [experiment])

  socket.on('timer', (data) => {
    console.log(data)
  })

}

export default ApiElement





