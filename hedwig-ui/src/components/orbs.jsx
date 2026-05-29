export default function Orb({ orbState }) {
  const isActive = orbState !== 'idle'

  const statusText = {
    idle:      'Awaiting your voice...',
    listening: 'Listening...',
    speaking:  'Speaking...',
  }[orbState]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '28px 0 22px' }}>
      <div style={{
        width: 116, height: 116,
        borderRadius: '50%',
        background: 'radial-gradient(circle at 35% 35%, rgba(201,168,76,.28) 0%, rgba(8,12,24,.85) 55%, rgba(8,12,24,1) 100%)',
        border: `2px solid ${isActive ? 'var(--gold)' : 'var(--gold-dim)'}`,
        boxShadow: isActive
          ? '0 0 50px rgba(201,168,76,.5), 0 0 100px rgba(201,168,76,.18), inset 0 0 40px rgba(201,168,76,.12)'
          : '0 0 28px rgba(201,168,76,.18), 0 0 60px rgba(201,168,76,.06), inset 0 0 28px rgba(201,168,76,.04)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 42,
        transition: 'all .4s',
        animation: orbState === 'listening' ? 'pulseOrb 1.6s ease-in-out infinite' : 'none',
      }}>
        🦉
      </div>
      <div style={{
        fontFamily: 'var(--font-serif)',
        fontSize: 11, letterSpacing: 3,
        color: isActive ? 'var(--gold)' : 'var(--text-dim)',
        textTransform: 'uppercase',
        marginTop: 13, transition: 'color .3s',
      }}>
        {statusText}
      </div>
    </div>
  )
}