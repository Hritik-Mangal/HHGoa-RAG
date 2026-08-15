export type VoiceOrbState =
  | 'idle'
  | 'hover'
  | 'listening'
  | 'transcribing'
  | 'retrieving'
  | 'generating'
  | 'complete'
  | 'error'

export type GuardrailDecision =
  | 'pass'
  | 'unsafe'
  | 'off_topic'
  | 'no_evidence'

export interface PipelineLatencies {
  stt_ms?: number
  embed_ms?: number
  retrieval_ms?: number
  guardrail_ms?: number
  generation_ms?: number
  total_ms?: number
}

export interface PassageChunk {
  chunk_id: string
  doc_id: string
  passage_id: string
  text: string
  lang: string
  strategy: string
  score?: number
}

export interface PipelineResponse {
  answer: string
  grounded: boolean
  confidence: number
  sources: string[]
  guardrail: GuardrailDecision
  latencies: PipelineLatencies
  retrieved_passages?: PassageChunk[]
  transcript?: string
  error?: string
}

export interface STTResponse {
  transcript: string
  language?: string
  confidence?: number
  latency_ms: number
}
