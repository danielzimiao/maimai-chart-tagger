import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { getTags, type AnalysisResult } from '../api'
import { SongBanner } from './SongBanner'

interface TagBrowsePanelProps {
  tag: string
  onClose: () => void
}

export function TagBrowsePanel({ tag, onClose }: TagBrowsePanelProps) {
  const [loading, setLoading] = useState(true)
  const [songs, setSongs] = useState<AnalysisResult['similar_songs']>([])

  useEffect(() => {
    setLoading(true)
    setSongs([])
    getTags(tag)
      .then((data) => {
        setSongs(data.songs)
      })
      .catch((err) => {
        console.error('Failed to load tag songs:', err)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [tag])

  return (
    <motion.div
      initial={{ x: 40, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 40, opacity: 0 }}
      transition={{ duration: 0.25 }}
      className="w-80 bg-gray-900 rounded-xl p-6 overflow-y-auto max-h-screen flex-shrink-0"
    >
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-white font-semibold">{tag}</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">
          ×
        </button>
      </div>
      {loading ? (
        <div className="text-gray-400">Loading...</div>
      ) : (
        <div className="flex flex-col gap-2">
          {songs.map((song, i) => (
            <SongBanner key={i} {...song} />
          ))}
        </div>
      )}
    </motion.div>
  )
}
