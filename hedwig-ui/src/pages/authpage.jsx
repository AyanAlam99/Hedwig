import { useState } from 'react'

export default function AuthPage({ onAuth }) {
  const [tab, setTab]     = useState('signup')
  const [name, setName]   = useState('')
  const [email, setEmail] = useState('')
  const [pass, setPass]   = useState('')
  const [error, setError] = useState('')

  function doSignup() {
    if (!name || !email || !pass) { setError('Please fill in all fields.'); return }
    if (pass.length < 6)          { setError('Password must be at least 6 characters.'); return }
    const user = { name, email }
    localStorage.setItem('hd_user', JSON.stringify(user))
    onAuth(user, false) 
  }

  function doLogin() {
    if (!email || !pass) { setError('Please fill in all fields.'); return }
    const saved = JSON.parse(localStorage.getItem('hd_user') || 'null')
    if (saved && saved.email === email) {
      const onboarded = !!localStorage.getItem('hd_onboarded')
      onAuth(saved, onboarded)
    } else {
      setError('Account not found. Please sign up first.')
    }
  }

  return (
    <div className="card">

      <div style={{
        display: 'flex', border: '1px solid var(--border)',
        borderRadius: 6, overflow: 'hidden', marginBottom: 28,
      }}>
        {['signup', 'login'].map(t => (
          <button key={t} onClick={() => { setTab(t); setError('') }} style={{
            flex: 1, padding: '10px', textAlign: 'center',
            fontFamily: 'var(--font-serif)', fontSize: 11,
            letterSpacing: 2, textTransform: 'uppercase',
            cursor: 'pointer', border: 'none', transition: 'all .2s',
            background: tab === t ? 'var(--gold-glow)' : 'transparent',
            color: tab === t ? 'var(--gold)' : 'var(--text-dim)',
          }}>
            {t === 'signup' ? 'Sign Up' : 'Sign In'}
          </button>
        ))}
      </div>

      {tab === 'signup' ? (
        <>
          <div className="card-title">Begin Your Journey</div>
          <div className="card-sub">Create your account to awaken Hedwig.</div>
          <div className="field">
            <label>Full Name</label>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Aryan Sharma" />
          </div>
          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="your@email.com" />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={pass} onChange={e => setPass(e.target.value)} placeholder="Choose a strong password" />
          </div>
          {error && <div style={{ color: '#b05050', fontSize: 13, marginBottom: 10 }}>{error}</div>}
          <button className="btn btn-gold btn-full" onClick={doSignup}>Create Account</button>
        </>
      ) : (
        <>
          <div className="card-title">Welcome Back</div>
          <div className="card-sub">Hedwig has been waiting for you.</div>
          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="your@email.com" />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={pass} onChange={e => setPass(e.target.value)} placeholder="Your password" />
          </div>
          {error && <div style={{ color: '#b05050', fontSize: 13, marginBottom: 10 }}>{error}</div>}
          <button className="btn btn-gold btn-full" onClick={doLogin}>Enter</button>
        </>
      )}
    </div>
  )
}