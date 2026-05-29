import { useState, useCallback } from 'react'
import { getContacts, addContact, removeContact } from '../api/hedwig'

export function useContacts() {
  const [contacts, setContacts] = useState({})
  const [loading, setLoading]   = useState(false)

  const refresh = useCallback(async () => {
    try {
      const data = await getContacts()
      setContacts(data.contacts || {})
    } catch (_) {}
  }, [])

  const add = useCallback(async (name, phone) => {
    setLoading(true)
    try {
      const data = await addContact(name, phone)
      if (data.success) await refresh()
      return data
    } finally {
      setLoading(false)
    }
  }, [refresh])


}