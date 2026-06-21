import { RELEASE_NOTES } from '../releaseNotes'

interface WhatsNewModalProps {
  onClose: () => void
}

export default function WhatsNewModal({ onClose }: WhatsNewModalProps) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <button className="modal-close-x" onClick={onClose} aria-label="Close">✕</button>

        <h2 className="modal-title">✨ What's New</h2>

        {RELEASE_NOTES.map(note => (
          <div key={note.version} className="release-card">
            <div className="release-meta">
              <span className="release-version">{note.version}</span>
              <span className="release-date">{note.date}</span>
            </div>
            <div className="release-title">{note.title}</div>
            <div className="release-body">{note.body}</div>
          </div>
        ))}

        <div className="guide-section">
          <h3>How it works</h3>
          <ul className="guide-steps">
            <li><strong>Log</strong> — Tap Log and type what you observed. Hit ⌘↵ or "Log It". No required fields.</li>
            <li><strong>Auto-tagging</strong> — The app detects competitor names, states, regions, and topics automatically.</li>
            <li><strong>Search</strong> — Find notes by typing anything — competitor name, city, topic, or free text.</li>
            <li><strong>Detail</strong> — Tap any note to see full text, all tags, and who logged it.</li>
          </ul>
          <button className="btn btn-primary" onClick={onClose}>Got it</button>
        </div>
      </div>
    </div>
  )
}
