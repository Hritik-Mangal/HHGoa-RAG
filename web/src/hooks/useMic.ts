/**
 * Raw PCM capture via ScriptProcessor → WAV encoder.
 * Bypasses MediaRecorder format issues entirely: we capture float32 samples
 * directly from the audio graph and encode them as 16-bit WAV ourselves.
 */
import { useCallback, useRef, useState } from 'react'

export type MicState = 'idle' | 'requesting' | 'recording' | 'error'

export interface UseMicReturn {
  state: MicState
  audioLevel: number
  startRecording: () => Promise<void>
  stopRecording: () => Promise<Blob | null>
  error: string | null
}

const BUFFER_SIZE = 4096
const TARGET_SR = 16000

export function useMic(): UseMicReturn {
  const [state, setState] = useState<MicState>('idle')
  const [audioLevel, setAudioLevel] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const ctxRef = useRef<AudioContext | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const samplesRef = useRef<Float32Array[]>([])
  const nativeSRRef = useRef<number>(44100)
  const rafRef = useRef<number>(0)

  const startRecording = useCallback(async () => {
    setError(null)
    setState('requesting')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const ctx = new AudioContext()
      ctxRef.current = ctx
      nativeSRRef.current = ctx.sampleRate

      const source = ctx.createMediaStreamSource(stream)

      // Analyser for waveform visualisation
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 256
      analyserRef.current = analyser
      source.connect(analyser)

      // ScriptProcessor captures raw PCM (mono, left channel)
      const processor = ctx.createScriptProcessor(BUFFER_SIZE, 1, 1)
      samplesRef.current = []
      processor.onaudioprocess = (e) => {
        const data = e.inputBuffer.getChannelData(0)
        samplesRef.current.push(new Float32Array(data))
      }
      source.connect(processor)
      processor.connect(ctx.destination)   // must be connected to run
      processorRef.current = processor

      // Level animation
      const tick = () => {
        const d = new Uint8Array(analyser.frequencyBinCount)
        analyser.getByteFrequencyData(d)
        setAudioLevel(d.reduce((a, b) => a + b, 0) / d.length / 255)
        rafRef.current = requestAnimationFrame(tick)
      }
      rafRef.current = requestAnimationFrame(tick)

      setState('recording')
    } catch (err: any) {
      setError(err?.message ?? 'Microphone access denied')
      setState('error')
    }
  }, [])

  const stopRecording = useCallback((): Promise<Blob | null> => {
    cancelAnimationFrame(rafRef.current)
    setAudioLevel(0)

    const processor = processorRef.current
    const ctx = ctxRef.current
    if (!processor || !ctx) return Promise.resolve(null)

    processor.disconnect()
    processorRef.current = null
    streamRef.current?.getTracks().forEach((t) => t.stop())
    setState('idle')

    // Combine all captured Float32 chunks
    const chunks = samplesRef.current
    samplesRef.current = []
    if (chunks.length === 0) return Promise.resolve(null)

    const nativeSR = nativeSRRef.current
    const combined = mergePCM(chunks)

    // Resample to 16kHz if needed, then encode as WAV
    ctx.close().catch(() => {})
    ctxRef.current = null

    return Promise.resolve(encodeWavBlob(resample(combined, nativeSR, TARGET_SR), TARGET_SR))
  }, [])

  return { state, audioLevel, startRecording, stopRecording, error }
}

// ---------------------------------------------------------------------------
// DSP helpers
// ---------------------------------------------------------------------------

function mergePCM(chunks: Float32Array[]): Float32Array {
  const total = chunks.reduce((n, c) => n + c.length, 0)
  const out = new Float32Array(total)
  let offset = 0
  for (const c of chunks) { out.set(c, offset); offset += c.length }
  return out
}

function resample(input: Float32Array, fromSR: number, toSR: number): Float32Array {
  if (fromSR === toSR) return input
  const ratio = fromSR / toSR
  const outLen = Math.floor(input.length / ratio)
  const out = new Float32Array(outLen)
  for (let i = 0; i < outLen; i++) {
    const src = i * ratio
    const lo = Math.floor(src)
    const hi = Math.min(lo + 1, input.length - 1)
    const frac = src - lo
    out[i] = input[lo] * (1 - frac) + input[hi] * frac
  }
  return out
}

function encodeWavBlob(samples: Float32Array, sampleRate: number): Blob {
  const buf = new ArrayBuffer(44 + samples.length * 2)
  const v = new DataView(buf)
  const s = (o: number, str: string) => { for (let i = 0; i < str.length; i++) v.setUint8(o + i, str.charCodeAt(i)) }

  s(0, 'RIFF'); v.setUint32(4, 36 + samples.length * 2, true)
  s(8, 'WAVE'); s(12, 'fmt ')
  v.setUint32(16, 16, true)
  v.setUint16(20, 1, true)             // PCM
  v.setUint16(22, 1, true)             // mono
  v.setUint32(24, sampleRate, true)
  v.setUint32(28, sampleRate * 2, true)
  v.setUint16(32, 2, true)
  v.setUint16(34, 16, true)
  s(36, 'data'); v.setUint32(40, samples.length * 2, true)

  let off = 44
  for (let i = 0; i < samples.length; i++) {
    const c = Math.max(-1, Math.min(1, samples[i]))
    v.setInt16(off, c < 0 ? c * 0x8000 : c * 0x7FFF, true)
    off += 2
  }
  return new Blob([buf], { type: 'audio/wav' })
}
