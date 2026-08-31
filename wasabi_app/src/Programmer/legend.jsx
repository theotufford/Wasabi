import { useContext, useState } from 'react'
import { useEffect } from 'react';
import { AppGlobalContext } from './AppGlobalContext';
import './css/legend.css'

function LegendElement(props) {
  const {experiment} = useContext(AppGlobalContext)
  const [selected_view, set_selected_view] = useState("color_map")
}
