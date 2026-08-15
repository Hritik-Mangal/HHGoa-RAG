import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { PassageChunk } from '../types'

interface SourceCardProps {
  passage: PassageChunk
  index: number
}

export function SourceCard({ passage, index }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false)
  const score = passage.score != null ? Math.round(passage.score * 100) / 100 : null
  const preview = passage.text.length > 120 ? passage.text.slice(0, 120) + '…' : passage.text

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: index * 0.06, ease: [0.22, 1, 0.36, 1] }}
      className="flex gap-3"
    >
      {/* Accent line */}
      <div
        className="w-0.5 rounded-full flex-shrink-0 self-stretch"
        style={{ background: 'var(--emerald-700)' }}
      />

      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="flex items-center gap-2">
            <span
              className="font-mono-data text-[9px] tracking-[0.14em] uppercase"
              style={{ color: 'var(--emerald-300)' }}
            >
              [{index + 1}]
            </span>
            <span className="font-mono-data text-[9px] text-[var(--text-muted)] truncate max-w-[140px]">
              {passage.chunk_id}
            </span>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {score != null && (
              <span className="font-mono-data text-[9px] text-[var(--text-muted)]">
                {score.toFixed(2)}
              </span>
            )}
            <span
              className="px-1.5 py-0.5 rounded text-[8px] uppercase tracking-widest"
              style={{ background: 'rgba(10,135,99,0.12)', color: 'var(--emerald-300)' }}
            >
              {passage.strategy}
            </span>
          </div>
        </div>

        {/* Text */}
        <button
          onClick={() => setExpanded((p) => !p)}
          className="text-left w-full text-xs leading-relaxed text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors duration-150"
        >
          <AnimatePresence initial={false}>
            {expanded ? (
              <motion.span
                key="full"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                {passage.text}
              </motion.span>
            ) : (
              <motion.span
                key="preview"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                {preview}
                {passage.text.length > 120 && (
                  <span className="ml-1 text-[var(--emerald-500)] text-[10px]">show more</span>
                )}
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>
    </motion.div>
  )
}
