import { useState, useEffect } from 'react'

export default function ContactSlots({ contacts, onAdd, onRemove, loading }) {
  const [name, setName]   = useState('')
  const [phone, setPhone] = useState('')

  const entries = Object.entries(contacts)

  async function handleAdd() {
    if (!name || !phone) return
    const res = await onAdd(name, phone)
    if (res?.success) { setName(''); setPhone('') }
  }

  return (
    <div>
      {entries.map(([n, p]) => (
        <div key={n} className="contact-slot">
          <div>
            <div className="contact-name">{n}</div>
            <div className="contact-phone">+{p}</div>
          </div>
          <button className="btn-danger" onClick={() => onRemove(n)}>Remove</button>
        </div>
      ))}

      {Array.from({ length: Math.max(0, 3 - entries.length) }, (_, i) => (
        <div key={i} className="slot-empty">Slot {entries.length + i + 1} — empty</div>
      ))}

      {entries.length < 3 && (
        <>
          <div className="divider" />
          <div style={{
            fontFamily: 'var(--font-serif)', fontSize: 10,
            letterSpacing: 2, color: 'var(--gold-dim)',
            textTransform: 'uppercase', marginBottom: 10,
          }}>
            Add Contact
          </div>
          <div className="row">
            <div className="field">
              <label>Name</label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Sufiyan" />
            </div>
            <div className="field">
              <label>Phone</label>
              <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="919876543210" />
            </div>
          </div>
          <button
            className="btn btn-gold btn-sm"
            onClick={handleAdd}
            disabled={loading || !name || !phone}
          >
            + Lock Contact
          </button>
        </>
      )}

      {entries.length >= 3 && (
        <div className="info-box" style={{ marginTop: 12, marginBottom: 0 }}>
          All 3 slots filled. Remove a contact to add another.
        </div>
      )}
    </div>
  )
}