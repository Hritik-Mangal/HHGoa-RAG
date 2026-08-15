import { motion } from 'framer-motion'
import { GlassPanel } from './GlassPanel'
import { MetricPill } from './MetricPill'
import type { PipelineResponse } from '../types'

interface AnswerCardProps {
  response: PipelineResponse
}

const CONFIDENCE_LABEL = (c: number) =>
  c >= 0.8 ? 'High' : c >= 0.5 ? 'Moderate' : 'Low'

export function AnswerCard({ response }: AnswerCardProps) {
  const { answer, grounded, confidence, sources, latencies } = response

  return (
    <GlassPanel glow={grounded ? 'emerald' : 'none'} className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-[10px] tracking-[0.18em] uppercase text-[var(--text-muted)]">Answer</p>
        <div className="flex items-center gap-2">
          <span
            className="px-2 py-0.5 rounded-full text-[9px] tracking-widest uppercase font-medium border"
            style={{
              color: grounded ? 'var(--success)' : 'var(--warning)',
              borderColor: grounded ? 'rgba(83,214,138,0.3)' : 'rgba(217,183,101,0.3)',
              background: grounded ? 'rgba(83,214,138,0.08)' : 'rgba(217,183,101,0.08)',
            }}
          >
            {grounded ? 'Grounded' : 'Ungrounded'}
          </span>
        </div>
      </div>

      {/* Divider */}
      <div className="h-px" style={{ background: 'var(--border-subtle)' }} />

      {/* Answer text */}
      <motion.p
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="text-base leading-relaxed text-[var(--text-primary)]"
        style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
      >
        {answer}
      </motion.p>

      {/* Footer: source count + confidence + latency */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.25, duration: 0.3 }}
        className="flex flex-wrap gap-2 items-center pt-2"
      >
        {sources.length > 0 && (
          <span className="text-[11px] text-[var(--text-muted)]">
            Grounded in {sources.length} passage{sources.length !== 1 ? 's' : ''}
          </span>
        )}
        <span className="text-[var(--text-muted)] text-[11px]">·</span>
        <span className="text-[11px] text-[var(--text-muted)]">
          Confidence: {CONFIDENCE_LABEL(confidence)}
        </span>
      </motion.div>

      {/* Latency breakdown pills */}
      {latencies.total_ms != null && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.3 }}
          className="flex flex-wrap gap-2 pt-1"
        >
          <MetricPill label="Total" value={latencies.total_ms} unit="ms" highlight />
          {latencies.retrieval_ms != null && (
            <MetricPill label="Retrieval" value={latencies.retrieval_ms} unit="ms" />
          )}
          {latencies.generation_ms != null && (
            <MetricPill label="Generation" value={latencies.generation_ms} unit="ms" />
          )}
          {latencies.stt_ms != null && (
            <MetricPill label="STT" value={latencies.stt_ms} unit="ms" />
          )}
        </motion.div>
      )}
    </GlassPanel>
  )
}
