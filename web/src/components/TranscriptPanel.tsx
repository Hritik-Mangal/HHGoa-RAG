import { AnimatePresence, motion } from 'framer-motion'
import { GlassPanel } from './GlassPanel'

interface TranscriptPanelProps {
  transcript: string | null
}

export function TranscriptPanel({ transcript }: TranscriptPanelProps) {
  return (
    <AnimatePresence>
      {transcript && (
        <GlassPanel
          key="transcript"
          className="p-5"
          glow="none"
        >
          <p className="text-[10px] tracking-[0.18em] uppercase text-[var(--text-muted)] mb-2">
            Transcript
          </p>
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed italic">
            "{transcript}"
          </p>
        </GlassPanel>
      )}
    </AnimatePresence>
  )
}
