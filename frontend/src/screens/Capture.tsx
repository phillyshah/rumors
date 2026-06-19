import { useCallback, useRef, useState } from 'react'
import { captureNote, getFeed, type Note, type User } from '../api'
import NoteCard from '../components/NoteCard'

interface CaptureProps {
  user: User
  onLogout: () => void
}

export default function Capture({ user, onLogout }: CaptureProps) {
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showToast, setShowToast] = useState(false)
  const [feed, setFeed] = useState<Note[]>([])
  const [feedLoaded, setFeedLoaded] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const loadFeed = useCallback(async () => {
    try {
      const notes = await getFeed(10)
      setFeed(notes)
      setFeedLoaded(true)
    } catch {}
  }, [])

  // Load feed on first render
  useState(() => { loadFeed() })

  const handleSubmit = async () => {
    const trimmed = text.trim()
    if (!trimmed || submitting) return
    setSubmitting(true)
    try {
      await captureNote(trimmed)
      setText('')
      textareaRef.current?.focus()
      if (toastTimer.current) clearTimeout(toastTimer.current)
      setShowToast(true)
      toastTimer.current = setTimeout(() => setShowToast(false), 2000)
      loadFeed()
    } catch (err: any) {
      alert('Failed to log: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="layout">
      {showToast && <div className="toast">✓ Logged</div>}

      <header className="page-header">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
          <path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" />
        </svg>
        <h1>Log Intel</h1>
        <span className="tagline">{user.display_name}</span>
      </header>

      <div className="content">
        <div className="capture-form">
          <div className="capture-hint">
            Log what you observed — competitor moves, rep chatter, account news. No required fields.
          </div>
          <textarea
            ref={textareaRef}
            className="capture-textarea"
            placeholder="What did you hear? Log observations, not accusations."
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
            rows={5}
          />
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={!text.trim() || submitting}
          >
            {submitting ? <><span className="spinner" style={{ borderTopColor: 'white' }} /> Logging…</> : 'Log It  ⌘↵'}
          </button>
        </div>

        {feedLoaded && feed.length > 0 && (
          <div style={{ marginTop: 28 }}>
            <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.5px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10 }}>
              Recent intel
            </div>
            {feed.map(note => <NoteCard key={note.id} note={note} />)}
          </div>
        )}
      </div>
    </div>
  )
}
