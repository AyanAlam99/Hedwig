export default function Logo({ subtitle = 'Your Personal Voice Companion' }) {
  return (
    <div style={{ textAlign: 'center', marginBottom: 36, animation: 'fadeDown .9s ease both' }}>
      <span style={{
        fontSize: 52, display: 'block',
        filter: 'drop-shadow(0 0 18px rgba(201,168,76,.55))',
        animation: 'float 4s ease-in-out infinite',
      }}>🦉</span>
      <div style={{
        fontFamily: 'var(--font-serif)', fontSize: 34, fontWeight: 700,
        color: 'var(--gold)', letterSpacing: 7,
        textShadow: '0 0 36px rgba(201,168,76,.35)', marginTop: 6,
      }}>HEDWIG</div>
      <div style={{
        fontStyle: 'italic', color: 'var(--text-dim)',
        fontSize: 14, letterSpacing: 2, marginTop: 3,
      }}>{subtitle}</div>
    </div>
  )
}