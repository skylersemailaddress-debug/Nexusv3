import { useEffect, useState } from 'react'

type HealthResponse = {
  status: string
  service: string
  timestamp: string
}

type ActionResponse = {
  result: string
  echo: string
  message: string
}

const apiBase = 'http://127.0.0.1:8000'

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [action, setAction] = useState<ActionResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${apiBase}/health`)
      .then(async (r) => {
        if (!r.ok) throw new Error(`Health failed: ${r.status}`)
        return r.json()
      })
      .then(setHealth)
      .catch((e: Error) => setError(e.message))
  }, [])

  async function runTest() {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${apiBase}/action/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'launch-commercial-slice' }),
      })
      if (!response.ok) throw new Error(`Action failed: ${response.status}`)
      const data = (await response.json()) as ActionResponse
      setAction(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ fontFamily: 'Inter, Arial, sans-serif', margin: 0, minHeight: '100vh', background: '#0b1020', color: '#f5f7fb' }}>
      <div style={{ maxWidth: 960, margin: '0 auto', padding: '48px 24px' }}>
        <div style={{ display: 'grid', gap: 20 }}>
          <div style={{ padding: 24, borderRadius: 20, background: '#111831', boxShadow: '0 8px 32px rgba(0,0,0,0.25)' }}>
            <div style={{ fontSize: 14, letterSpacing: 1, textTransform: 'uppercase', opacity: 0.7 }}>Nexus v3</div>
            <h1 style={{ margin: '8px 0 8px', fontSize: 40 }}>Commercial Runtime Slice</h1>
            <p style={{ margin: 0, opacity: 0.85, lineHeight: 1.5 }}>
              One executable authority surface: one UI, one API, one visible action loop.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 20 }}>
            <div style={{ padding: 24, borderRadius: 20, background: '#111831' }}>
              <div style={{ fontSize: 14, opacity: 0.7 }}>API health</div>
              <div style={{ marginTop: 12, fontSize: 28, fontWeight: 700 }}>{health?.status ?? 'checking'}</div>
              <div style={{ marginTop: 8, opacity: 0.8 }}>{health?.service ?? 'nexus-control unavailable'}</div>
            </div>

            <div style={{ padding: 24, borderRadius: 20, background: '#111831' }}>
              <div style={{ fontSize: 14, opacity: 0.7 }}>Runtime action</div>
              <button
                onClick={runTest}
                disabled={loading}
                style={{ marginTop: 14, padding: '12px 16px', borderRadius: 12, border: 0, cursor: 'pointer', fontWeight: 700 }}
              >
                {loading ? 'Running...' : 'Run test action'}
              </button>
              <div style={{ marginTop: 12, opacity: 0.9 }}>{action?.message ?? 'No action executed yet.'}</div>
            </div>
          </div>

          <div style={{ padding: 24, borderRadius: 20, background: '#111831' }}>
            <div style={{ fontSize: 14, opacity: 0.7 }}>What this proves</div>
            <ul style={{ lineHeight: 1.8, opacity: 0.9 }}>
              <li>Runtime authority is consolidated under <code>runtime/</code>.</li>
              <li>The UI is a real package, not extracted artifact debris.</li>
              <li>The control plane now has a real boot path and a real health endpoint.</li>
              <li>The first commercial loop can now be swapped in behind <code>/action/test</code>.</li>
            </ul>
            {error ? <div style={{ color: '#ff8d8d' }}>Error: {error}</div> : null}
          </div>
        </div>
      </div>
    </div>
  )
}
