import { motion } from 'framer-motion'
import logoSrc from '../assets/logo.png'

export function RoyalHeader() {
  return (
    <header className="relative z-10 flex items-center justify-between px-4 sm:px-6 md:px-8 py-4 sm:py-5">
      {/* Brand mark */}
      <motion.div
        initial={{ opacity: 0, x: -16 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="flex items-center"
      >
        <img
          src={logoSrc}
          alt="Logo"
          className="h-10 w-auto object-contain"
        />
      </motion.div>

      {/* Nav pills */}
      <motion.nav
        initial={{ opacity: 0, x: 16 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
        className="flex items-center gap-1"
      >
        <a
          href="/"
          className="px-4 py-1.5 text-xs font-medium tracking-widest uppercase text-[var(--text-secondary)] hover:text-[var(--emerald-300)] transition-colors duration-200"
        >
          Query
        </a>
        <a
          href="/analytics"
          className="px-4 py-1.5 text-xs font-medium tracking-widest uppercase text-[var(--text-secondary)] hover:text-[var(--emerald-300)] transition-colors duration-200"
        >
          Analytics
        </a>
      </motion.nav>
    </header>
  )
}
