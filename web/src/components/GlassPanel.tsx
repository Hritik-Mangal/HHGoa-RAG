import { motion } from 'framer-motion'
import type { HTMLAttributes, ReactNode } from 'react'

interface GlassPanelProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  glow?: 'none' | 'emerald' | 'gold'
  animate?: boolean
}

export function GlassPanel({
  children,
  glow = 'none',
  animate = true,
  className = '',
  ...props
}: GlassPanelProps) {
  const glowStyle =
    glow === 'emerald'
      ? '0 0 40px rgba(91, 214, 163, 0.12)'
      : glow === 'gold'
      ? '0 0 40px rgba(200, 165, 90, 0.14)'
      : 'none'

  const Comp = animate ? motion.div : 'div'
  const animateProps = animate
    ? {
        initial: { opacity: 0, y: 8 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] },
      }
    : {}

  return (
    <Comp
      {...(animateProps as any)}
      style={{ boxShadow: `0 20px 70px rgba(0,0,0,0.24), inset 0 1px 0 rgba(255,255,255,0.035)${glowStyle ? `, ${glowStyle}` : ''}` }}
      className={`glass relative overflow-hidden ${className}`}
      {...props}
    >
      {children}
    </Comp>
  )
}
