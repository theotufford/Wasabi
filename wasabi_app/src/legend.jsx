import { useContext, useState } from 'react'
import { useEffect } from 'react';
import { ExperimentContext } from './ExperimentContext';
import './legend.css'

function LegendElement(props) {
  const {experiment} = useContext(ExperimentContext)
  const [selected_view, set_selected_view] = useState("color_map")
}
