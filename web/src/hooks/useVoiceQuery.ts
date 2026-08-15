import { useCallback, useReducer } from 'react'
import { transcribeAudio, queryRAG } from '../lib/api'
import { embedQuery } from '../lib/embedder'
import { useMic } from './useMic'
import type { PipelineResponse, VoiceOrbState } from '../types'

interface QueryState {
  orbState: VoiceOrbState
  transcript: string | null
  response: PipelineResponse | null
  error: string | null
}

type Action =
  | { type: 'START_LISTENING' }
  | { type: 'TRANSCRIBING' }
  | { type: 'RETRIEVING' }
  | { type: 'GENERATING' }
  | { type: 'COMPLETE'; response: PipelineResponse; transcript: string }
  | { type: 'ERROR'; message: string }
  | { type: 'RESET' }

function reducer(state: QueryState, action: Action): QueryState {
  switch (action.type) {
    case 'START_LISTENING':
      return { ...state, orbState: 'listening', error: null }
    case 'TRANSCRIBING':
      return { ...state, orbState: 'transcribing' }
    case 'RETRIEVING':
      return { ...state, orbState: 'retrieving' }
    case 'GENERATING':
      return { ...state, orbState: 'generating' }
    case 'COMPLETE':
      return {
        ...state,
        orbState: 'complete',
        response: action.response,
        transcript: action.transcript,
        error: null,
      }
    case 'ERROR':
      return { ...state, orbState: 'error', error: action.message }
    case 'RESET':
      return { orbState: 'idle', transcript: null, response: null, error: null }
    default:
      return state
  }
}

const initialState: QueryState = {
  orbState: 'idle',
  transcript: null,
  response: null,
  error: null,
}

export function useVoiceQuery(language = 'hi-IN') {
  const [state, dispatch] = useReducer(reducer, initialState)
  const mic = useMic()

  const startListening = useCallback(async () => {
    dispatch({ type: 'START_LISTENING' })
    await mic.startRecording()
  }, [mic])

  const stopAndProcess = useCallback(async () => {
    const blob = await mic.stopRecording()
    if (!blob) {
      dispatch({ type: 'ERROR', message: 'No audio captured' })
      return
    }

    try {
      // STT
      dispatch({ type: 'TRANSCRIBING' })
      const sttResult = await transcribeAudio(blob, language)
      const transcript = sttResult.transcript

      // Embed (client-side; null means server will handle it)
      dispatch({ type: 'RETRIEVING' })
      const qv = await embedQuery(transcript)

      // RAG query
      dispatch({ type: 'GENERATING' })
      const response = await queryRAG(transcript, qv ?? [], language)

      dispatch({ type: 'COMPLETE', response, transcript })
    } catch (err: any) {
      dispatch({ type: 'ERROR', message: err?.message ?? 'Pipeline error' })
    }
  }, [mic, language])

  const submitText = useCallback(async (query: string) => {
    if (!query.trim()) return
    dispatch({ type: 'RETRIEVING' })
    try {
      const qv = await embedQuery(query.trim())
      dispatch({ type: 'GENERATING' })
      const response = await queryRAG(query.trim(), qv ?? [], language)
      dispatch({ type: 'COMPLETE', response, transcript: query.trim() })
    } catch (err: any) {
      dispatch({ type: 'ERROR', message: err?.message ?? 'Pipeline error' })
    }
  }, [language])

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' })
  }, [])

  return {
    ...state,
    audioLevel: mic.audioLevel,
    micState: mic.state,
    startListening,
    stopAndProcess,
    submitText,
    reset,
  }
}
