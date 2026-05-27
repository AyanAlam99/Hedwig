import { useState , useEffect , useRef } from "react" 
import { getLogs } from "../api/hedwig"

export function useLogs(active = true) 
{
    const [logs, setLogs] = useState([])
    const [orbState, setOrbState] = useState('idle')
    const countRef = useRef(0)

    
}
