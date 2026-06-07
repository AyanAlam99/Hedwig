import { useState, useCallback } from 'react'
import { getIntegrations } from '../api/hedwig'

const CONNECTED_STATUSES = ['connected', 'active']

export function useIntegrations() {
  const [statusMap, setStatusMap] = useState({})
  const [loaded, setLoaded] = useState(false)

  const refresh = useCallback(async () => {
    const res = await getIntegrations()
    if (res?.integrations) {
      const map = {}
      res.integrations.forEach(i => { map[i.provider] = i.status })
      setStatusMap(map)
    }
    setLoaded(true)
  }, [])

  const isConnected = useCallback((feature) => {
    if (!feature?.provider) return null 
    return CONNECTED_STATUSES.includes(statusMap[feature.provider])
  }, [statusMap])

  return { statusMap, isConnected, refresh, loaded }
}
