const corners = [
  { top: 14, left: 14,  border: '2px 0 0 2px' },
  { top: 14, right: 14, border: '2px 2px 0 0' },
  { bottom: 14, left: 14,  border: '0 0 2px 2px' },
  { bottom: 14, right: 14, border: '0 2px 2px 0' },
]

export default function CornerFrames() {
  return (
    <>
      {corners.map((c, i) => (
        <div key={i} style={{
          position: 'fixed',
          width: 70, height: 70,
          borderColor: 'var(--gold-dim)',
          borderStyle: 'solid',
          borderWidth: c.border,
          opacity: .35,
          zIndex: 1,
          pointerEvents: 'none',
          ...c,
        }} />
      ))}
    </>
  )
}