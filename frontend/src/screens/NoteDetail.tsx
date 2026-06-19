import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getNote, type NoteDetail as NoteDetailType, formatFullTime, formatRelativeTime } from '../api'
import TagChip from '../components/TagChip'

export default function NoteDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [note, setNote] = useState<NoteDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    getNote(Number(id))
      .then(setNote)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="loading-center"><div className="spinner" /></div>
  if (error || !note) return (
    <div className="content">
      <a href="#" className="back-btn" onClick={e => { e.preventDefault(); navigate(-1) }}>
        ← Back
      </a>
      <div className="error-msg">{error || 'Note not found'}</div>
    </div>
  )

  return (
    <div className="layout">
      <header className="page-header">
        <button
          className="nav-btn"
          onClick={() => navigate(-1)}
          style={{ color: 'white', minHeight: 'auto', padding: '0 8px 0 0' }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
          </svg>
        </button>
        <h1>Intel Detail</h1>
        <span className="tagline">{formatRelativeTime(note.created_at)}</span>
      </header>

      <div className="content">
        <div className="detail-card">
          <div className="detail-raw">{note.raw_text}</div>

          {note.summary && (
            <div style={{ marginBottom: 16, padding: '10px 14px', background: 'var(--blue-light)', borderRadius: 8, fontSize: 14, lineHeight: 1.5 }}>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--blue)', marginBottom: 4 }}>Summary</div>
              {note.summary}
            </div>
          )}

          <div className="detail-section">
            <div className="detail-label">Tags</div>
            <div className="card-tags">
              {note.competitors.map(c => <TagChip key={c} type="competitor" value={c} />)}
              {note.distributors.map(d => <TagChip key={d} type="competitor" value={d} />)}
              {note.states.map(s => <TagChip key={s} type="state" value={s} />)}
              {note.regions.map(r => <TagChip key={r} type="region" value={r} />)}
              {note.topics.filter(t => t !== 'other').map(t => <TagChip key={t} type="topic" value={t} />)}
              {note.source_confidence && <TagChip type="confidence" value={note.source_confidence} />}
            </div>
          </div>

          {note.entities.length > 0 && (
            <div className="detail-section">
              <div className="detail-label">Entities mentioned</div>
              <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>
                {note.entities.map((e, i) => (
                  <span key={i}>
                    {typeof e === 'string' ? e : e.name ?? JSON.stringify(e)}
                    {i < note.entities.length - 1 ? ', ' : ''}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="detail-section">
            <div className="detail-label">Geo scope</div>
            <span style={{ fontSize: 14, textTransform: 'capitalize' }}>{note.geo_scope}</span>
          </div>

          <div className="detail-attribution">
            <span>
              <strong>Logged by</strong> {note.author_display_name}
            </span>
            <span title={formatFullTime(note.created_at)}>
              {formatFullTime(note.created_at)}
            </span>
          </div>

          {note.enriched_at && (
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
              AI-enriched · {note.extraction_method}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
