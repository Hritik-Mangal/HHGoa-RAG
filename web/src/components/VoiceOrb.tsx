import { motion, AnimatePresence } from 'framer-motion'
import type { VoiceOrbState } from '../types'

interface VoiceOrbProps {
  state: VoiceOrbState
  audioLevel: number   // 0–1
  /** Desktop click-to-toggle mode; mobile uses hold (onPointerDown/Up) */
  clickMode?: boolean
  onClick?: () => void
  onPointerDown?: () => void
  onPointerUp?: () => void
  disabled?: boolean
  size?: number
}

const ORB_LABEL_CLICK: Record<VoiceOrbState, string> = {
  idle: 'Click to speak',
  hover: 'Click to speak',
  listening: 'Click to send',
  transcribing: 'Transcribing…',
  retrieving: 'Searching…',
  generating: 'Generating…',
  complete: 'Done',
  error: 'Error — try again',
}

const ORB_LABEL_HOLD: Record<VoiceOrbState, string> = {
  idle: 'Hold to speak',
  hover: 'Hold to speak',
  listening: 'Release to send',
  transcribing: 'Transcribing…',
  retrieving: 'Searching…',
  generating: 'Generating…',
  complete: 'Done',
  error: 'Error — try again',
}

export function VoiceOrb({
  state,
  audioLevel,
  clickMode = false,
  onClick,
  onPointerDown,
  onPointerUp,
  disabled,
  size = 140,
}: VoiceOrbProps) {
  const isActive = state === 'listening'
  const isProcessing = state === 'transcribing' || state === 'retrieving' || state === 'generating'
  const isComplete = state === 'complete'
  const isError = state === 'error'

  const ORB_LABEL = clickMode ? ORB_LABEL_CLICK : ORB_LABEL_HOLD
  const ringSize = size * 1.43   // ambient ring ~200px at size=140

  const coreColor = isError
    ? 'rgba(228,124,124,0.85)'
    : isComplete
    ? 'rgba(83,214,138,0.85)'
    : isActive
    ? 'rgba(25,169,116,0.90)'
    : 'rgba(25,169,116,0.55)'

  const ringColor = isComplete ? 'var(--gold-500)' : 'var(--emerald-500)'

  // Event handlers — desktop click-toggle vs mobile hold
  const buttonProps = clickMode
    ? {
        onClick: isProcessing ? undefined : onClick,
      }
    : {
        onPointerDown: isProcessing ? undefined : onPointerDown,
        onPointerUp: isProcessing ? undefined : onPointerUp,
        onPointerLeave: isActive ? onPointerUp : undefined,
      }

  return (
    <div className="relative flex flex-col items-center gap-4 select-none">
      {/* Orbit nodes during retrieval */}
      <AnimatePresence>
        {state === 'retrieving' && (
          <>
            {[0, 120, 240].map((deg) => (
              <motion.div
                key={deg}
                className="absolute w-2.5 h-2.5 rounded-full bg-[var(--emerald-300)]"
                style={{ top: '50%', left: '50%', marginTop: -5, marginLeft: -5 }}
                initial={{ rotate: deg, translateX: 0, opacity: 0 }}
                animate={{ rotate: deg + 360, translateX: size * 0.43, opacity: [0, 0.9, 0.9, 0] }}
                exit={{ opacity: 0 }}
                transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
              />
            ))}
          </>
        )}
      </AnimatePresence>

      {/* Outer ambient ring */}
      <motion.div
        className="absolute rounded-full border"
        style={{ width: ringSize, height: ringSize, borderColor: ringColor, opacity: 0.15 }}
        animate={
          isActive
            ? { scale: [1, 1.3, 1.1, 1.4, 1], opacity: [0.15, 0.3, 0.2, 0.35, 0.15] }
            : { scale: [1, 1.04, 1], opacity: [0.12, 0.18, 0.12] }
        }
        transition={{ duration: isActive ? 0.8 + audioLevel : 5, repeat: Infinity, ease: 'easeInOut' }}
      />

      {/* Main orb button */}
      <motion.button
        aria-label={ORB_LABEL[state]}
        aria-pressed={isActive}
        disabled={disabled || isProcessing}
        {...buttonProps}
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          background: `radial-gradient(circle at 35% 35%, rgba(91,214,163,0.3) 0%, ${coreColor} 55%, rgba(6,75,56,0.9) 100%)`,
          border: `1.5px solid ${isComplete ? 'var(--gold-500)' : 'var(--border-green)'}`,
          boxShadow: isActive
            ? '0 0 40px rgba(25,169,116,0.4), 0 0 80px rgba(25,169,116,0.15)'
            : isComplete
            ? '0 0 30px rgba(200,165,90,0.3)'
            : '0 0 20px rgba(25,169,116,0.12)',
          cursor: isProcessing ? 'wait' : 'pointer',
          position: 'relative',
        }}
        whileHover={!isProcessing ? { scale: 1.04 } : undefined}
        whileTap={!isProcessing ? { scale: 0.97 } : undefined}
        animate={
          isProcessing
            ? { rotate: [0, 360] }
            : isComplete
            ? { scale: [1, 1.06, 1] }
            : {}
        }
        transition={
          isProcessing
            ? { duration: 4, repeat: Infinity, ease: 'linear' }
            : isComplete
            ? { duration: 0.5, ease: [0.22, 1, 0.36, 1] }
            : { duration: 0.2 }
        }
      >
        {/* Inner core glow */}
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: `radial-gradient(circle at 50% 50%, ${coreColor} 0%, transparent 70%)`,
            opacity: 0.6 + audioLevel * 0.4,
          }}
        />

        {/* Icon */}
        <div className="relative z-10 flex items-center justify-center w-full h-full">
          {isProcessing ? (
            <motion.div
              className="w-5 h-5 rounded-full border-2 border-t-transparent"
              style={{ borderColor: 'var(--emerald-300)' }}
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            />
          ) : (
            <MicIcon active={isActive} complete={isComplete} error={isError} size={size} />
          )}
        </div>
      </motion.button>

      {/* State label */}
      <motion.p
        key={state}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="text-xs tracking-[0.14em] uppercase"
        style={{
          color: isError
            ? 'var(--danger)'
            : isComplete
            ? 'var(--gold-400)'
            : isActive
            ? 'var(--emerald-300)'
            : 'var(--text-muted)',
        }}
      >
        {ORB_LABEL[state]}
      </motion.p>
    </div>
  )
}

function MicIcon({ active, complete, error, size }: {
  active: boolean; complete: boolean; error: boolean; size: number
}) {
  const color = error ? 'var(--danger)' : complete ? 'var(--gold-400)' : active ? 'var(--emerald-300)' : 'var(--text-secondary)'
  const iconSize = Math.round(size * 0.2)
  return (
    <svg
      width={iconSize}
      height={iconSize}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" x2="12" y1="19" y2="22" />
    </svg>
  )
}
