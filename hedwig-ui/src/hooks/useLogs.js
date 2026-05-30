import { useState, useEffect, useRef } from 'react'

export function useLogs() {
  const [logs, setLogs]         = useState([])
  const [orbState, setOrbState] = useState('idle')
  const countRef                = useRef(0)

  useEffect(() => {
    async function poll() {
      try {
        const res  = await fetch('/api/logs')
        const data = await res.json()
        const incoming = data.logs || []
        if (incoming.length !== countRef.current) {
          countRef.current = incoming.length
          setLogs([...incoming])
          const last = incoming[incoming.length - 1]
          if (!last) return
          const m = last.msg
          if (m.includes('Listening'))        setOrbState('listening')
          else if ( m.includes('Wake word'))    setOrbState('listening')
          else if (m.includes('Back to sleep') || m.includes('Ready')) setOrbState('idle')
          else if (last.sender === 'hedwig')                       setOrbState('speaking')
        }
      } catch(e) {
        console.error('useLogs error:', e)
      }
    }

    poll() 
    const id = setInterval(poll, 1000)
    return () => clearInterval(id)
  }, [])

  return { logs, orbState }
}