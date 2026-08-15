import { motion } from 'framer-motion'

interface WaveformVisualizerProps {
  level: number       // 0–1
  active: boolean
  bars?: number
}

export function WaveformVisualizer({ level, active, bars = 20 }: WaveformVisualizerProps) {
  return (
    <div className="flex items-center justify-center gap-[3px] h-10" aria-hidden>
      {Array.from({ length: bars }).map((_, i) => {
        const base = 0.15 + 0.25 * Math.abs(Math.sin((i / bars) * Math.PI))
        const height = active ? base + level * 0.6 : base * 0.5
        const delay = (i / bars) * 0.15

        return (
          <motion.div
            key={i}
            className="w-[2px] rounded-full"
            style={{
              background: i % 5 === 0 ? 'var(--gold-500)' : 'var(--emerald-500)',
              opacity: active ? 0.7 + level * 0.3 : 0.25,
              transformOrigin: '50% 50%',
            }}
            animate={{ scaleY: height * 4 }}
            initial={{ scaleY: base * 2 }}
            transition={{ duration: 0.12, delay, ease: 'easeOut' }}
          />
        )
      })}
    </div>
  )
}
