interface TagCardProps {
  tag: string
  onClick: (tag: string) => void
}

const TAG_COLORS: Record<string, string> = {
  'Trill': 'bg-purple-600 text-white hover:bg-purple-500',
  'Stream': 'bg-blue-600 text-white hover:bg-blue-500',
  'Stamina': 'bg-red-600 text-white hover:bg-red-500',
  'Tech/Crossover': 'bg-yellow-600 text-white hover:bg-yellow-500',
  'Slide-Heavy': 'bg-green-600 text-white hover:bg-green-500',
  'Hand-Alternation': 'bg-orange-600 text-white hover:bg-orange-500',
  'Balanced': 'bg-gray-600 text-gray-400',
}

const DEFAULT_COLOR = 'bg-indigo-600 text-white hover:bg-indigo-500'

export function TagCard({ tag, onClick }: TagCardProps) {
  const isBalanced = tag === 'Balanced'
  const colorClass = TAG_COLORS[tag] ?? DEFAULT_COLOR

  return (
    <span
      className={`rounded-full px-4 py-1 text-sm font-medium cursor-pointer transition-colors ${colorClass}`}
      style={isBalanced ? { pointerEvents: 'none' } : undefined}
      onClick={() => onClick(tag)}
    >
      {tag}
    </span>
  )
}
