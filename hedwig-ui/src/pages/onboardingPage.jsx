import { useState } from 'react'
import FeatureCard from '../components/featureCard'
import ActivationPanel from '../components/activationPanel'
import FEATURES from '../features'

export default function OnboardingPage({ user, activated, onActivate, onContinue, showToast }) {
  const [activeFeature, setActiveFeature] = useState(null)

  function openPanel(id) {
    const f = FEATURES.find(x => x.id === id)
    setActiveFeature(f)
  }

  function closePanel() { setActiveFeature(null) }

  function handleActivated(id) {
    onActivate(id)
  }

  const firstName = user?.name?.split(' ')[0] || 'Friend'

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div style={{ textAlign: 'center', marginBottom: 32, animation: 'fadeDown .6s ease both' }}>
        <div style={{ fontFamily: 'var(--font-serif)', fontSize: 26, color: 'var(--gold)', letterSpacing: 4 }}>
          Welcome, {firstName}
        </div>
        <div style={{ fontStyle: 'italic', color: 'var(--text-dim)', fontSize: 15, marginTop: 6 }}>
          Activate the powers you need. Everything else works out of the box.
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 14, width: '100%', maxWidth: 720,
      }}>
        {FEATURES.map((f, i) => (
          <FeatureCard
            key={f.id}
            feature={f}
            activated={!!activated[f.id]}
            onActivate={openPanel}
            delay={i * 0.07}
          />
        ))}

        <div style={{
          gridColumn: '1 / -1',
          background: 'var(--navy-card)',
          border: '1px dashed var(--border-dim)',
          borderRadius: 'var(--radius)',
          padding: '14px 20px',
          textAlign: 'center',
          fontStyle: 'italic',
          color: 'var(--text-dim)',
          fontSize: 15,
        }}>
          🔮 Many more integrations coming — Notion, Slack, Reminders, Music recognition & more
        </div>
      </div>

      <div style={{ marginTop: 32, textAlign: 'center' }}>
        <button
          className="btn btn-gold"
          style={{ padding: '13px 48px', fontSize: 13 }}
          onClick={onContinue}
        >
          Enter Hedwig's Chamber →
        </button>
        <div style={{ marginTop: 12 }}>
          <button className="lbtn" onClick={onContinue}>
            Skip for now — activate later from Settings
          </button>
        </div>
      </div>

      {activeFeature && (
        <ActivationPanel
          feature={activeFeature}
          onClose={closePanel}
          onActivated={handleActivated}
          showToast={showToast}
        />
      )}
    </div>
  )
}