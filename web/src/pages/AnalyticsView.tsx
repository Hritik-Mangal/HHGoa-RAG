import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { GlassPanel } from '../components/GlassPanel'
import { MetricPill } from '../components/MetricPill'
import { healthCheck } from '../lib/api'

interface BenchmarkData {
  n_queries?: number
  tier1?: {
    p50_ms: number
    p70_ms: number
    p100_ms: number
    description: string
  }
  note?: string
}

export function AnalyticsView() {
  const [health, setHealth] = useState<{
    status: string
    index_loaded: boolean
    index_size: number
    model?: string
  } | null>(null)

  const [benchmarks, setBenchmarks] = useState<BenchmarkData>({
    n_queries: 30,
    tier1: {
      p50_ms: 0,
      p70_ms: 0,
      p100_ms: 0,
      description: 'embed + retrieval + guardrails (no LLM)',
    },
    note: 'Run python scripts/benchmark.py to populate these values.',
  })

  useEffect(() => {
    healthCheck()
      .then(setHealth)
      .catch(() => setHealth(null))
  }, [])

  useEffect(() => {
    fetch('/benchmark-results.json')
      .then(r => (r.ok ? r.json() : null))
      .then(data => { if (data) setBenchmarks(data) })
      .catch(() => {})
  }, [])

  return (
    <div className="flex-1 px-4 sm:px-6 pb-10 sm:pb-12 max-w-4xl mx-auto w-full space-y-6 sm:space-y-8 mt-6 sm:mt-8">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <p className="text-[10px] tracking-[0.22em] uppercase text-[var(--gold-500)] mb-2">
          Intelligence Console
        </p>
        <h2 className="font-display text-4xl font-medium text-[var(--text-primary)]">
          Pipeline Analytics
        </h2>
      </motion.div>

      {/* System health */}
      <GlassPanel className="p-6 space-y-4">
        <p className="text-[10px] tracking-[0.18em] uppercase text-[var(--text-muted)]">
          System Status
        </p>
        <div className="flex flex-wrap gap-2 sm:gap-4">
          <MetricPill
            label="Status"
            value={health?.status ?? 'Connecting…'}
            highlight={health?.status === 'ok'}
          />
          <MetricPill
            label="Index Size"
            value={health?.index_size ?? null}
            unit=" chunks"
          />
          <MetricPill
            label="Index"
            value={health?.index_loaded ? 'Loaded' : 'Offline'}
          />
          <MetricPill
            label="Model"
            value={health?.model ?? '—'}
          />
        </div>
      </GlassPanel>

      {/* Latency benchmarks — Tier 1 */}
      <GlassPanel className="p-6 space-y-6">
        <div>
          <p className="text-[10px] tracking-[0.18em] uppercase text-[var(--text-muted)] mb-1">
            Pipeline Performance — Tier 1
          </p>
          <p className="text-xs text-[var(--text-muted)]">
            {benchmarks.tier1?.description}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 sm:gap-4">
          <MetricPill label="P50" value={benchmarks.tier1?.p50_ms || '—'} unit="ms" highlight />
          <MetricPill label="P70" value={benchmarks.tier1?.p70_ms || '—'} unit="ms" />
          <MetricPill label="P100" value={benchmarks.tier1?.p100_ms || '—'} unit="ms" />
          <MetricPill label="Queries" value={benchmarks.n_queries ?? '—'} />
        </div>
        {benchmarks.note && (
          <p className="text-[11px] text-[var(--text-muted)] italic">{benchmarks.note}</p>
        )}
      </GlassPanel>

      {/* Pipeline breakdown */}
      <GlassPanel className="p-6 space-y-4">
        <p className="text-[10px] tracking-[0.18em] uppercase text-[var(--text-muted)]">
          Pipeline Breakdown
        </p>
        <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] flex-wrap">
          {['STT', 'Embed', 'Retrieval', 'Guardrails', 'Generation'].map((stage, i, arr) => (
            <span key={stage} className="flex items-center gap-2">
              <span
                className="px-3 py-1 rounded border text-[var(--emerald-300)]"
                style={{ borderColor: 'var(--border-green)', background: 'rgba(10,135,99,0.08)' }}
              >
                {stage}
              </span>
              {i < arr.length - 1 && <span className="text-[var(--text-muted)]">→</span>}
            </span>
          ))}
        </div>
        <p className="text-xs text-[var(--text-muted)]">
          Tier 1 target: Embed + Retrieval + Guardrails &lt; 200ms.{' '}
          STT and Generation are reported separately as Tier 2.
        </p>
      </GlassPanel>

      {/* Chunking strategies */}
      <GlassPanel className="p-6 space-y-4">
        <p className="text-[10px] tracking-[0.18em] uppercase text-[var(--text-muted)]">
          Chunking Strategy Comparison
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-[var(--text-secondary)]">
            <thead>
              <tr className="border-b" style={{ borderColor: 'var(--border-subtle)' }}>
                {['Strategy', 'Description', 'Recall@5', 'MRR', 'Latency'].map((h) => (
                  <th key={h} className="pb-2 text-left font-medium text-[var(--text-muted)] pr-4 whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="space-y-2">
              {[
                ['A — Fixed', 'Token windows + overlap', '—', '—', '—'],
                ['B — Semantic', 'Sentence-boundary splits', '—', '—', '—'],
                ['C — Metadata', 'Whole passage, no splits', '—', '—', '—'],
                ['D — Adaptive ✓', 'Hybrid: short→whole, long→semantic', '—', '—', '—'],
              ].map(([strat, desc, recall, mrr, lat]) => (
                <tr key={strat} className="border-b" style={{ borderColor: 'var(--border-subtle)' }}>
                  <td className="py-2 pr-4 font-medium text-[var(--text-primary)] whitespace-nowrap">{strat}</td>
                  <td className="py-2 pr-4 text-[var(--text-muted)]">{desc}</td>
                  <td className="py-2 pr-4 font-mono-data">{recall}</td>
                  <td className="py-2 pr-4 font-mono-data">{mrr}</td>
                  <td className="py-2 font-mono-data">{lat}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-[var(--text-muted)] italic">
          Run python scripts/evaluate.py --strategy A/B/C/D to populate metrics.
        </p>
      </GlassPanel>
    </div>
  )
}
