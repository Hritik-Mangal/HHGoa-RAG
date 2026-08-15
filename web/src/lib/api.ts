import type { PipelineResponse, STTResponse } from '../types'

const BASE = ''  // same origin on Vercel; proxied to localhost:8000 in dev

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }))
    throw new Error(err.detail ?? err.error ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function transcribeAudio(
  audioBlob: Blob,
  language = 'hi-IN',
): Promise<STTResponse> {
  const b64 = await blobToBase64(audioBlob)
  // useMic always converts to WAV before returning the blob
  return post<STTResponse>('/api/stt', { audio_b64: b64, format: 'wav', mime_type: 'audio/wav', language })
}

export async function queryRAG(
  transcript: string,
  queryVector: number[],
  language = 'hi-IN',
  topK = 5,
): Promise<PipelineResponse> {
  return post<PipelineResponse>('/api/query', {
    transcript,
    query_vector: queryVector,
    language,
    top_k: topK,
  })
}

export async function healthCheck(): Promise<{ status: string; index_loaded: boolean; index_size: number }> {
  const res = await fetch('/api/health')
  return res.json()
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      // Strip the data URL prefix (data:audio/...;base64,)
      const b64 = result.split(',')[1]
      resolve(b64)
    }
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}
