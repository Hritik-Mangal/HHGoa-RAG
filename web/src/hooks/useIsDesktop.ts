import { useEffect, useState } from 'react'

// Matches Tailwind's lg breakpoint (1024px)
const DESKTOP_MQ = '(min-width: 1024px)'

export function useIsDesktop(): boolean {
  const [isDesktop, setIsDesktop] = useState<boolean>(() =>
    typeof window !== 'undefined'
      ? window.matchMedia(DESKTOP_MQ).matches
      : true,
  )

  useEffect(() => {
    const mq = window.matchMedia(DESKTOP_MQ)
    const handler = (e: MediaQueryListEvent) => setIsDesktop(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  return isDesktop
}
