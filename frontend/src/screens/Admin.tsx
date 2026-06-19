import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  getAdminCompetitors, createCompetitor, deleteCompetitor,
  getAdminDistributors, createDistributor, deleteDistributor,
  getAdminTopics, createTopicKeyword, deleteTopicKeyword,
  type User,
} from '../api'

interface AdminProps { user: User }

type TabKey = 'competitors' | 'distributors' | 'topics'

export default function Admin({ user }: AdminProps) {
  const navigate = useNavigate()
  const [tab, setTab] = useState<TabKey>('competitors')

  if (!user.is_admin) {
    navigate('/')
    return null
  }

  return (
    <div className="layout">
      <header className="page-header">
        <h1>Admin</h1>
        <span className="tagline">Gazetteer Management</span>
      </header>
      <div className="content">
        <div className="tab-bar">
          {(['competitors', 'distributors', 'topics'] as TabKey[]).map(t => (
            <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {tab === 'competitors' && <CompetitorsTab />}
        {tab === 'distributors' && <DistributorsTab />}
        {tab === 'topics' && <TopicsTab />}
      </div>
    </div>
  )
}

function CompetitorsTab() {
  const [rows, setRows] = useState<any[]>([])
  const [canonical, setCanonical] = useState('')
  const [aliases, setAliases] = useState('')
  const [loading, setLoading] = useState(true)

  const load = () => getAdminCompetitors().then(setRows).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canonical.trim()) return
    await createCompetitor(canonical.trim(), aliases.split(',').map(a => a.trim()).filter(Boolean))
    setCanonical(''); setAliases('')
    load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this competitor?')) return
    await deleteCompetitor(id)
    load()
  }

  if (loading) return <div className="loading-center"><div className="spinner" /></div>

  return (
    <div className="admin-section">
      <h2>Competitors ({rows.length})</h2>
      <table className="admin-table">
        <thead><tr><th>Canonical</th><th>Aliases</th><th>Active</th><th></th></tr></thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.id}>
              <td><strong>{r.canonical}</strong></td>
              <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{r.aliases.join(', ')}</td>
              <td>{r.active ? '✓' : '—'}</td>
              <td><button className="btn btn-danger btn-sm" onClick={() => handleDelete(r.id)}>Del</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <form onSubmit={handleAdd} className="admin-add-form">
        <input placeholder="Canonical name" value={canonical} onChange={e => setCanonical(e.target.value)} required />
        <input placeholder="Aliases (comma-separated)" value={aliases} onChange={e => setAliases(e.target.value)} />
        <button type="submit" className="btn btn-primary btn-sm">Add</button>
      </form>
    </div>
  )
}

function DistributorsTab() {
  const [rows, setRows] = useState<any[]>([])
  const [canonical, setCanonical] = useState('')
  const [aliases, setAliases] = useState('')
  const [region, setRegion] = useState('')
  const [loading, setLoading] = useState(true)

  const load = () => getAdminDistributors().then(setRows).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canonical.trim()) return
    await createDistributor(
      canonical.trim(),
      aliases.split(',').map(a => a.trim()).filter(Boolean),
      region.trim() || undefined,
    )
    setCanonical(''); setAliases(''); setRegion('')
    load()
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Delete?')) return
    await deleteDistributor(id)
    load()
  }

  if (loading) return <div className="loading-center"><div className="spinner" /></div>

  return (
    <div className="admin-section">
      <h2>Distributors ({rows.length})</h2>
      {rows.length === 0 && <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 16 }}>No distributors yet.</p>}
      {rows.length > 0 && (
        <table className="admin-table">
          <thead><tr><th>Canonical</th><th>Aliases</th><th>Region</th><th></th></tr></thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id}>
                <td><strong>{r.canonical}</strong></td>
                <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{r.aliases.join(', ')}</td>
                <td>{r.region ?? '—'}</td>
                <td><button className="btn btn-danger btn-sm" onClick={() => handleDelete(r.id)}>Del</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <form onSubmit={handleAdd} className="admin-add-form">
        <input placeholder="Canonical name" value={canonical} onChange={e => setCanonical(e.target.value)} required />
        <input placeholder="Aliases (comma-separated)" value={aliases} onChange={e => setAliases(e.target.value)} />
        <input placeholder="Region (optional)" value={region} onChange={e => setRegion(e.target.value)} />
        <button type="submit" className="btn btn-primary btn-sm">Add</button>
      </form>
    </div>
  )
}

function TopicsTab() {
  const [rows, setRows] = useState<any[]>([])
  const [topic, setTopic] = useState('')
  const [keyword, setKeyword] = useState('')
  const [loading, setLoading] = useState(true)

  const load = () => getAdminTopics().then(setRows).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!topic.trim() || !keyword.trim()) return
    await createTopicKeyword(topic.trim(), keyword.trim())
    setTopic(''); setKeyword('')
    load()
  }

  const handleDelete = async (t: string, k: string) => {
    await deleteTopicKeyword(t, k)
    load()
  }

  if (loading) return <div className="loading-center"><div className="spinner" /></div>

  // Group by topic
  const byTopic: Record<string, string[]> = {}
  for (const r of rows) {
    byTopic[r.topic] = byTopic[r.topic] ?? []
    byTopic[r.topic].push(r.keyword)
  }

  return (
    <div className="admin-section">
      <h2>Topic Keywords</h2>
      {Object.entries(byTopic).map(([t, keywords]) => (
        <div key={t} style={{ marginBottom: 16 }}>
          <div style={{ fontWeight: 700, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.4px', color: 'var(--orange)', marginBottom: 6 }}>{t}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {keywords.map(k => (
              <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, background: 'var(--orange-light)', color: 'var(--orange)', padding: '3px 10px', borderRadius: 20, fontSize: 12 }}>
                {k}
                <button onClick={() => handleDelete(t, k)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontSize: 14, lineHeight: 1, padding: 0 }}>×</button>
              </span>
            ))}
          </div>
        </div>
      ))}
      <form onSubmit={handleAdd} className="admin-add-form" style={{ marginTop: 16 }}>
        <input placeholder="Topic (e.g. pricing)" value={topic} onChange={e => setTopic(e.target.value)} required />
        <input placeholder="Keyword" value={keyword} onChange={e => setKeyword(e.target.value)} required />
        <button type="submit" className="btn btn-primary btn-sm">Add</button>
      </form>
    </div>
  )
}
