import { AnimatePresence, motion } from 'framer-motion'
import { useCallback, useRef, useState } from 'react'
import { AnswerCard } from '../components/AnswerCard'
import { GlassPanel } from '../components/GlassPanel'
import { PipelineStatus } from '../components/PipelineStatus'
import { SourceCard } from '../components/SourceCard'
import { TranscriptPanel } from '../components/TranscriptPanel'
import { VoiceOrb } from '../components/VoiceOrb'
import { WaveformVisualizer } from '../components/WaveformVisualizer'
import { useIsDesktop } from '../hooks/useIsDesktop'
import { useVoiceQuery } from '../hooks/useVoiceQuery'

export function HomePage() {
  const [showSources, setShowSources] = useState(false)
  const [textQuery, setTextQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const isDesktop = useIsDesktop()

  const {
    orbState,
    transcript,
    response,
    error,
    audioLevel,
    startListening,
    stopAndProcess,
    submitText,
    reset,
  } = useVoiceQuery('hi-IN')

  const isListening = orbState === 'listening'
  const isProcessing = ['transcribing', 'retrieving', 'generating'].includes(orbState)
  const hasResult = orbState === 'complete' && response != null

  // Desktop: single click toggles recording on/off
  const handleOrbClick = useCallback(() => {
    if (isListening) {
      stopAndProcess()
    } else if (!isProcessing) {
      startListening()
    }
  }, [isListening, isProcessing, startListening, stopAndProcess])

  const orbSize = isDesktop ? 140 : 116

  return (
    <div className="flex-1 flex flex-col items-center px-4 sm:px-6 pb-10 sm:pb-12 gap-6 sm:gap-8 md:gap-10">

      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="text-center mt-8 sm:mt-10 md:mt-14 px-2"
      >
        <p className="text-[9px] sm:text-[10px] tracking-[0.22em] uppercase text-[var(--gold-500)] mb-2 sm:mb-3">
          Voice · Retrieval · Intelligence
        </p>
        <h1 className="font-display text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-medium text-[var(--text-primary)] leading-[1.1] mb-2 sm:mb-3">
          The Voice of Knowledge
        </h1>
        <p className="text-xs sm:text-sm text-[var(--text-muted)] tracking-wider">
          Ask naturally. Discover precisely.
        </p>
      </motion.div>

      {/* Waveform */}
      <WaveformVisualizer
        level={audioLevel}
        active={isListening}
        bars={isDesktop ? 24 : 16}
      />

      {/* Voice Orb — desktop: click toggle / mobile: hold */}
      {isDesktop ? (
        <VoiceOrb
          state={orbState}
          audioLevel={audioLevel}
          clickMode
          onClick={handleOrbClick}
          disabled={isProcessing}
          size={orbSize}
        />
      ) : (
        <VoiceOrb
          state={orbState}
          audioLevel={audioLevel}
          onPointerDown={startListening}
          onPointerUp={isListening ? stopAndProcess : () => {}}
          disabled={isProcessing}
          size={orbSize}
        />
      )}

      {/* Pipeline state label */}
      <PipelineStatus state={orbState} />

      {/* Text query fallback */}
      <AnimatePresence>
        {orbState === 'idle' && (
          <motion.form
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            onSubmit={(e) => { e.preventDefault(); submitText(textQuery); setTextQuery('') }}
            className="flex gap-2 w-full max-w-xs sm:max-w-sm md:max-w-md"
          >
            <input
              ref={inputRef}
              value={textQuery}
              onChange={(e) => setTextQuery(e.target.value)}
              placeholder="Or type a question…"
              className="flex-1 min-w-0 px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm text-[var(--text-primary)] outline-none"
              style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-green)' }}
            />
            <button
              type="submit"
              disabled={!textQuery.trim()}
              className="flex-shrink-0 px-3 sm:px-4 py-2 rounded-xl text-[10px] sm:text-xs font-medium tracking-wider uppercase transition-opacity disabled:opacity-40"
              style={{ background: 'var(--emerald-700)', color: 'var(--text-primary)' }}
            >
              Ask
            </button>
          </motion.form>
        )}
      </AnimatePresence>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="px-4 py-2 rounded-xl text-xs sm:text-sm max-w-xs sm:max-w-md text-center"
            style={{
              background: 'rgba(228,124,124,0.08)',
              border: '1px solid rgba(228,124,124,0.2)',
              color: 'var(--danger)',
            }}
          >
            {error}
            <button
              onClick={reset}
              className="ml-2 sm:ml-3 text-[10px] uppercase tracking-widest opacity-70 hover:opacity-100"
            >
              Dismiss
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results area */}
      <AnimatePresence>
        {hasResult && response && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
            className="w-full max-w-xs sm:max-w-xl md:max-w-2xl space-y-3 sm:space-y-4"
          >
            <TranscriptPanel transcript={transcript} />
            <AnswerCard response={response} />

            {/* Sources accordion */}
            {(response.retrieved_passages?.length ?? 0) > 0 && (
              <GlassPanel className="p-4 sm:p-5 space-y-4">
                <button
                  onClick={() => setShowSources((p) => !p)}
                  className="flex items-center justify-between w-full"
                >
                  <p className="text-[9px] sm:text-[10px] tracking-[0.18em] uppercase text-[var(--text-muted)]">
                    Retrieved Sources ({response.retrieved_passages!.length})
                  </p>
                  <span className="text-[9px] sm:text-[10px] text-[var(--emerald-300)]">
                    {showSources ? 'Hide' : 'Show'}
                  </span>
                </button>
                <AnimatePresence>
                  {showSources && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden space-y-4"
                    >
                      {response.retrieved_passages!.map((p, i) => (
                        <SourceCard key={p.chunk_id} passage={p} index={i} />
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </GlassPanel>
            )}

            {/* Reset */}
            <div className="text-center">
              <button
                onClick={() => { reset(); setShowSources(false) }}
                className="text-[10px] sm:text-xs tracking-widest uppercase text-[var(--text-muted)] hover:text-[var(--emerald-300)] transition-colors duration-200"
              >
                Ask another question
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tagline when idle */}
      {orbState === 'idle' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="flex flex-wrap items-center justify-center gap-3 sm:gap-6 text-[9px] sm:text-[10px] tracking-[0.14em] uppercase text-[var(--text-muted)]"
        >
          <span>Grounded retrieval</span>
          <span className="text-[var(--gold-500)] opacity-50">◆</span>
          <span>Fast inference</span>
          <span className="text-[var(--gold-500)] opacity-50">◆</span>
          <span className="hidden sm:inline">MSMARCO-XI</span>
        </motion.div>
      )}
    </div>
  )
}
