import { useState , useEffect , useRef } from "react" 
import { getLogs } from "../api/hedwig"

export function useLogs(active = true) 
{
    const [logs, setLogs] = useState([])
    const [orbState, setOrbState] = useState('idle')
    const countRef = useRef(0)

    useEffect(()=>{
        if(!active)return 

        const id = setInterval(async () =>{
            try{
                const data = await getLogs()
                const incoming = data.logs || []
                if (incoming.length == countRef.length) return 
                countRef.current = incoming.length
                setLogs([...incoming])

                const last = incoming[incoming.length -1 ]
                if(!last) return 
                const  m = last.msg 
                if (m.includes('Listening') )  setOrbState('listening')
                else if (m.includes('Wake'))   setOrbState('listening')
                else if (m.includes('Back to sleep') || m.includes('Ready')) setOrbState('idle')
                else if (last.sender === 'hedwig') setOrbState('speaking')    
            }
        catch (_) {}
        },1000)
        return () =>clearInterval(id)
    },[active])

    return {logs , orbState}
}

