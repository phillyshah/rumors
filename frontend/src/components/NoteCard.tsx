import { Link } from 'react-router-dom'
import { type Note, formatRelativeTime, formatFullTime } from '../api'
import TagChip from './TagChip'

interface NoteCardProps {
  note: Note
}

export default function NoteCard({ note }: NoteCardProps) {
  const snippet = note.summary ?? note.raw_text

  return (
    <Link to={`/notes/${note.id}`} className="card">
      <div className="card-snippet">{snippet}</div>
      <div className="card-tags">
        {note.competitors.map(c => <TagChip key={c} type="competitor" value={c} />)}
        {note.states.map(s => <TagChip key={s} type="state" value={s} />)}
        {note.regions.filter(r => !note.states.some(s => true)).slice(0, 2).map(r => (
          <TagChip key={r} type="region" value={r} />
        ))}
        {note.topics.filter(t => t !== 'other').map(t => <TagChip key={t} type="topic" value={t} />)}
        {note.source_confidence && note.source_confidence !== 'medium' && (
          <TagChip type="confidence" value={note.source_confidence} />
        )}
      </div>
      <div className="card-meta">
        <span className="card-timestamp" title={formatFullTime(note.created_at)}>
          {formatRelativeTime(note.created_at)}
        </span>
        <span className="card-full-date">{formatFullTime(note.created_at)}</span>
      </div>
    </Link>
  )
}
