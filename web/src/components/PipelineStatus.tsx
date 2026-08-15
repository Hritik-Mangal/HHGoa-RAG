import { AnimatePresence, motion } from 'framer-motion'
import type { VoiceOrbState } from '../types'

const STATUS_LABELS: Record<VoiceOrbState, string> = {
  idle: 'READY',
  hover: 'READY',
  listening: 'LISTENING',
  transcribing: 'TRANSCRIBING',
  retrieving: 'RETRIEVING',
  generating: 'GENERATING',
  complete: 'COMPLETE',
  error: 'ERROR',
}

const STATUS_COLORS: Record<VoiceOrbState, string> = {
  idle: 'var(--text-muted)',
  hover: 'var(--emerald-300)',
  listening: 'var(--emerald-500)',
  transcribing: 'var(--gold-400)',
  retrieving: 'var(--emerald-300)',
  generating: 'var(--gold-500)',
  complete: 'var(--success)',
  error: 'var(--danger)',
}

interface PipelineStatusProps {
  state: VoiceOrbState
}

export function PipelineStatus({ state }: PipelineStatusProps) {
  return (
    <div className="flex items-center gap-2 justify-center h-6">
      <AnimatePresence mode="wait">
        <motion.div
          key={state}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.15 }}
          className="flex items-center gap-2"
        >
          {/* Pulse dot */}
          <motion.div
            className="w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: STATUS_COLORS[state] }}
            animate={
              state === 'listening' || state === 'retrieving' || state === 'generating'
                ? { scale: [1, 1.4, 1], opacity: [1, 0.6, 1] }
                : { scale: 1, opacity: 1 }
            }
            transition={{ duration: 1, repeat: Infinity }}
          />
          <span
            className="font-mono-data text-[10px] tracking-[0.2em]"
            style={{ color: STATUS_COLORS[state] }}
          >
            {STATUS_LABELS[state]}
          </span>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
