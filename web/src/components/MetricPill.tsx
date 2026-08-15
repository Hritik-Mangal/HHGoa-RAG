interface MetricPillProps {
  label: string
  value: string | number | null | undefined
  unit?: string
  highlight?: boolean
}

export function MetricPill({ label, value, unit = '', highlight = false }: MetricPillProps) {
  const display = value == null ? '—' : `${typeof value === 'number' ? Math.round(value) : value}${unit}`

  return (
    <div
      className="flex flex-col items-center px-4 py-2 rounded-xl border"
      style={{
        background: 'rgba(16,42,30,0.5)',
        borderColor: highlight ? 'var(--gold-500)' : 'var(--border-green)',
      }}
    >
      <span
        className="font-mono-data text-lg font-medium"
        style={{ color: highlight ? 'var(--gold-400)' : 'var(--emerald-300)' }}
      >
        {display}
      </span>
      <span className="text-[9px] tracking-[0.18em] uppercase mt-0.5 text-[var(--text-muted)]">
        {label}
      </span>
    </div>
  )
}
