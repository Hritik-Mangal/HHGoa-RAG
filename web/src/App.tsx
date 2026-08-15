import { useEffect } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { HomePage } from './pages/HomePage'
import { AnalyticsView } from './pages/AnalyticsView'

export default function App() {
  useEffect(() => {
    fetch('/api/health').catch(() => {})
  }, [])

  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AppShell>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/analytics" element={<AnalyticsView />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}
