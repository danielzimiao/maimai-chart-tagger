const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface SongBannerProps {
  name: string
  difficulty: number | null
  bg_image_url: string | null
}

export function SongBanner({ name, difficulty, bg_image_url }: SongBannerProps) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-800">
      {bg_image_url ? (
        <img
          src={`${API_BASE}${bg_image_url}`}
          alt={name}
          className="w-12 h-12 object-cover rounded flex-shrink-0"
        />
      ) : (
        <div className="w-12 h-12 bg-gray-700 rounded flex-shrink-0" />
      )}
      <span className="flex-1 text-white text-sm truncate">{name}</span>
      {difficulty !== null && (
        <span className="text-gray-400 text-sm">{difficulty.toFixed(1)}</span>
      )}
    </div>
  )
}
