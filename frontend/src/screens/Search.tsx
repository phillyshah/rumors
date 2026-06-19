import { useCallback, useEffect, useRef, useState } from 'react'
import { searchNotes, type Note, type User } from '../api'
import NoteCard from '../components/NoteCard'

interface SearchProps {
  user: User
  onLogout: () => void
}

export default function Search({ user, onLogout }: SearchProps) {
  const [query, setQuery] = useState('')
  const [notes, setNotes] = useState<Note[]>([])
  const [synthesis, setSynthesis] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [synthesize, setSynthesize] = useState(false)
  const [searched, setSearched] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const doSearch = useCallback(async (q: string, synth: boolean) => {
    setLoading(true)
    try {
      const res = await searchNotes({ q: q || undefined, synthesize: synth, limit: 30 })
      setNotes(res.notes)
      setSynthesis(res.synthesis)
      setTotal(res.total)
      setSearched(true)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [])

  // Debounced search as user types
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      doSearch(query, synthesize)
    }, 300)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [query, synthesize, doSearch])

  // Load recent on mount
  useEffect(() => { doSearch('', false) }, [doSearch])

  return (
    <div className="layout">
      <header className="page-header">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <h1>Search Intel</h1>
        <span className="tagline">{user.display_name}</span>
      </header>

      <div className="content">
        <div className="search-bar-wrap">
          <input
            className="search-input"
            type="search"
            placeholder='Try "Stryker FL" or "pricing Southeast"'
            value={query}
            onChange={e => setQuery(e.target.value)}
            autoFocus
          />
          {loading && <div className="spinner" />}
        </div>

        <label className="search-toggle">
          <input
            type="checkbox"
            checked={synthesize}
            onChange={e => setSynthesize(e.target.checked)}
            style={{ marginRight: 4 }}
          />
          AI summary (Claude)
        </label>

        {synthesis && (
          <div className="synthesis-box">
            <div className="synthesis-label">AI Summary</div>
            {synthesis}
          </div>
        )}

        {searched && (
          <div className="result-count">
            {total === 0 ? 'No results' : `${total} result${total !== 1 ? 's' : ''}${query ? ` for "${query}"` : ''}`}
          </div>
        )}

        {notes.length === 0 && searched && !loading && (
          <div className="empty-state">
            <p>🔍</p>
            <p style={{ fontSize: 15 }}>No intel found{query ? ` for "${query}"` : ''}</p>
          </div>
        )}

        {notes.map(note => <NoteCard key={note.id} note={note} />)}
      </div>
    </div>
  )
}
