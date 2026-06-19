interface TagChipProps {
  type: 'competitor' | 'state' | 'region' | 'topic' | 'confidence' | 'method'
  value: string
}

const TOPIC_LABELS: Record<string, string> = {
  account_movement: 'account mvmt',
  distributor_health: 'distributor',
  'm&a': 'M&A',
}

export default function TagChip({ type, value }: TagChipProps) {
  const label = type === 'topic' ? (TOPIC_LABELS[value] ?? value) : value
  return <span className={`chip chip-${type === 'confidence' ? `confidence-${value}` : type}`}>{label}</span>
}
