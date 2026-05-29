const badgeStyles = {
  free:      { bg: 'rgba(201,168,76,.1)',  border: 'rgba(201,168,76,.2)',  color: 'var(--gold-dim)' },
  api:       { bg: 'rgba(139,26,26,.12)', border: 'rgba(139,26,26,.3)',   color: '#b06060' },
  activated: { bg: 'rgba(26,112,112,.15)', border: 'rgba(26,112,112,.4)', color: '#5dbdbd' },
}

export default function FeatureCard({ feature, activated, onActivate, delay = 0 }) {
  const { id, icon, name, desc, badge, autoActivate } = feature
  const isOn = activated || autoActivate

  const badgeStyle = isOn ? badgeStyles.activated : badgeStyles[badge] || badgeStyles.api
  const badgeLabel = isOn ? 'Active' : badge === 'free' ? 'Free' : 'Needs API'

  return (
    <div style={{
      background: 'var(--navy-card)',
      border: `1px solid ${isOn ? 'rgba(26,112,112,.45)' : badge === 'free' ? 'rgba(201,168,76,.12)' : 'rgba(201,168,76,.08)'}`,
      borderRadius: 'var(--radius)',
      padding: 20,
      display: 'flex', flexDirection: 'column',
      boxShadow: isOn ? '0 0 18px rgba(26,112,112,.12)' : 'none',
      transition: 'border-color .25s, box-shadow .25s',
      animation: `fadeUp .5s ease ${delay}s both`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <span style={{ fontSize: 30, lineHeight: 1 }}>{icon}</span>
        <span style={{
          fontFamily: 'var(--font-serif)', fontSize: 9,
          letterSpacing: 1.5, padding: '3px 8px', borderRadius: 10,
          textTransform: 'uppercase',
          background: badgeStyle.bg,
          border: `1px solid ${badgeStyle.border}`,
          color: badgeStyle.color,
        }}>
          {badgeLabel}
        </span>
      </div>

      <div style={{
        fontFamily: 'var(--font-serif)', fontSize: 14,
        color: 'var(--gold-pale)', letterSpacing: 1, marginBottom: 4,
      }}>
        {name}
      </div>

      <div style={{
        fontSize: 14, color: 'var(--text-dim)',
        lineHeight: 1.45, marginBottom: 14, flex: 1,
      }}>
        {desc}
      </div>

      {isOn ? (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          fontFamily: 'var(--font-serif)', fontSize: 11,
          color: '#5dbdbd', letterSpacing: 1,
        }}>
          <span style={{
            width: 7, height: 7, borderRadius: '50%',
            background: '#5dbdbd', boxShadow: '0 0 6px #5dbdbd',
          }} />
          Connected
        </div>
      ) : badge === 'free' ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-serif)', fontSize: 11, color: '#5dbdbd', letterSpacing: 1 }}>
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#5dbdbd', boxShadow: '0 0 6px #5dbdbd' }} />
          Ready
        </div>
      ) : (
        <button
          className="btn btn-gold btn-sm"
          style={{ width: '100%' }}
          onClick={() => onActivate(id)}
        >
          Activate →
        </button>
      )}
    </div>
  )
}