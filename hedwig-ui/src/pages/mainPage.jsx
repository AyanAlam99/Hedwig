import { useEffect } from 'react'
import Orb from '../components/orbs'
import TranscriptFeed from '../components/transcriptFeed'
import ContactSlots from '../components/contactSlots'
import { useLogs } from '../hooks/useLogs'
import { useContacts } from '../hooks/useContacts'

export default function MainPage({ user, onOpenSettings }) {
  const { logs, orbState } = useLogs(true)
  const { contacts, refresh, add, remove, loading } = useContacts()

  useEffect(() => { refresh() }, [])

  const chips = Object.keys(contacts)

  return (
    <div style={{ width: '100%', maxWidth: 660, animation: 'fadeUp .7s ease both' }}>

    
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '9px 15px',
        background: 'rgba(0,0,0,.28)',
        border: '1px solid var(--border)',
        borderRadius: 7, marginBottom: 14,
        fontFamily: 'var(--font-serif)', fontSize: 10, letterSpacing: 1.5,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 5,
            padding: '3px 10px', borderRadius: 12,
            fontFamily: 'var(--font-serif)', fontSize: 9, letterSpacing: 1,
            background: 'rgba(26,112,112,.18)',
            border: '1px solid rgba(26,112,112,.35)',
            color: '#5dbdbd',
          }}>
            <span style={{
              width: 5, height: 5, borderRadius: '50%',
              background: 'currentColor',
              animation: 'blink 1.4s ease-in-out infinite',
            }} />
            Hedwig Active
          </span>
          {user?.name && (
            <span style={{ color: 'var(--text-dim)' }}>· {user.name}</span>
          )}
        </div>
        <button className="lbtn" onClick={onOpenSettings}>⚙ Settings</button>
      </div>

     
      {chips.length > 0 && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
          {chips.map(n => (
            <div key={n} style={{
              display: 'flex', alignItems: 'center', gap: 5,
              padding: '5px 12px',
              background: 'rgba(201,168,76,.07)',
              border: '1px solid var(--border)',
              borderRadius: 14,
              fontFamily: 'var(--font-serif)', fontSize: 11,
              color: 'var(--gold-pale)', letterSpacing: .5,
            }}>
              🕯 {n}
            </div>
          ))}
        </div>
      )}

      <Orb orbState={orbState} />
      <TranscriptFeed logs={logs} />

    </div>
  )
}
export function SettingsPage({ onBack, showToast }) {
  const { contacts, refresh, add, remove, loading } = useContacts()
  useEffect(() => { refresh() }, [])

  return (
    <div className="card" style={{ maxWidth: 540 }}>
      <div className="card-title">⚙ Settings</div>
      <div className="card-sub">Manage integrations and trusted contacts.</div>
      <div className="divider" />
      <div style={{
        fontFamily: 'var(--font-serif)', fontSize: 10,
        letterSpacing: 2, color: 'var(--gold-dim)',
        textTransform: 'uppercase', marginBottom: 10,
      }}>
        WhatsApp Trusted Contacts
      </div>
      <ContactSlots
        contacts={contacts}
        onAdd={async (n, p) => {
          const res = await add(n, p)
          if (res?.success) showToast(`${n} added.`, 'success')
          else showToast(res?.message, 'error')
          return res
        }}
        onRemove={async (n) => {
          const res = await remove(n)
          if (res?.success) showToast(`${n} removed.`, 'success')
          return res
        }}
        loading={loading}
      />
      <div className="divider" style={{ marginTop: 20 }} />
      <button className="btn btn-ghost btn-full" onClick={onBack}>← Back to Hedwig</button>
    </div>
  )
}