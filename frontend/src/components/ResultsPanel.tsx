import { TagCard } from './TagCard'
import { SongBanner } from './SongBanner'
import type { AnalysisResult } from '../api'

interface ResultsPanelProps {
  results: AnalysisResult
  onTagClick: (tag: string) => void
}

export function ResultsPanel({ results, onTagClick }: ResultsPanelProps) {
  const { difficulty, tags, similar_songs } = results
  const topSongs = similar_songs.slice(0, 3)

  return (
    <div className="flex flex-col gap-6 w-full max-w-md bg-gray-900 rounded-xl p-6">
      {difficulty !== null && (
        <div className="flex items-center gap-2">
          <span className="text-gray-400 text-sm">Expected Difficulty</span>
          <span className="text-white text-2xl font-bold">{difficulty.toFixed(1)}</span>
        </div>
      )}

      {tags.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-gray-400 text-xs uppercase tracking-wider">Tags</span>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <TagCard key={tag} tag={tag} onClick={onTagClick} />
            ))}
          </div>
        </div>
      )}

      {topSongs.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-gray-400 text-xs uppercase tracking-wider">Similar Songs</span>
          <div className="flex flex-col gap-2">
            {topSongs.map((song, i) => (
              <SongBanner
                key={i}
                name={song.name}
                difficulty={song.difficulty}
                bg_image_url={song.bg_image_url}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
