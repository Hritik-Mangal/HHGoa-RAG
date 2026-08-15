import type { ReactNode } from 'react'
import { RoyalHeader } from './RoyalHeader'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell relative z-10 min-h-dvh flex flex-col">
      <RoyalHeader />
      <main className="flex-1 flex flex-col">{children}</main>
      <footer className="py-4 text-center">
        <p className="text-xs text-[var(--text-muted)] tracking-widest uppercase">
          HH Goa 2026 · Voice RAG · #RAGInGoa
        </p>
      </footer>
    </div>
  )
}
