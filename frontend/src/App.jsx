import React, { useEffect, useMemo, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:5000'

async function api(path, opts) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  if (res.status === 204) return null
  return res.json()
}

export default function App() {
  const [items, setItems] = useState([])
  const [fetchedAt, setFetchedAt] = useState('')
  const [q, setQ] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const filtered = useMemo(() => {
    return items
  }, [items])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const data = await api(`/api/summary?q=${encodeURIComponent(q)}`)
      setItems(data.items)
      setFetchedAt(data.fetched_at || '')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const id = setInterval(load, 60_000) // refresh every minute in UI
    return () => clearInterval(id)
  }, [q])

  async function triggerIngest() {
    setError('')
    try {
      await api('/api/ingest', { method: 'POST' })
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>ARSO Hourly Air Quality</h1>
        <div className="muted">Backend: {API_BASE}</div>
      </header>

      <section className="row">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filter by key (e.g., PM10, O3, station name)..."
        />
        <button onClick={load}>Search</button>
        <button onClick={triggerIngest}>Fetch now</button>
      </section>

      {fetchedAt && (
        <div className="muted">Latest dataset: {new Date(fetchedAt).toLocaleString()}</div>
      )}

      {error && <div className="error">{String(error)}</div>}
      {loading && <div className="muted">Loading...</div>}

      <ul className="list">
        {filtered.map((row, idx) => (
          <li key={idx}>
            <code style={{ opacity: 0.8 }}>{row.key}</code>
            <div style={{ justifySelf: 'end' }}>
              <strong>{row.value}</strong>
              {row.unit ? <span className="muted"> {row.unit}</span> : null}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
