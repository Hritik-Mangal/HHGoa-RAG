/**
 * Client-side query embedding via Transformers.js (Xenova/multilingual-e5-small).
 * Loaded lazily; cached after first use.
 *
 * Kept in its own module so it's easily replaceable with a server-side embed API
 * if Transformers.js proves impractical on a given target.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let pipeline: ((text: string | string[], opts?: any) => Promise<any>) | null = null
let loadPromise: Promise<void> | null = null

async function loadModel(): Promise<void> {
  const { pipeline: createPipeline } = await import('@huggingface/transformers')
  const p = await createPipeline(
    'feature-extraction',
    'Xenova/multilingual-e5-small',
    { revision: 'main' },
  )
  pipeline = async (text) => {
    const out = await p(text, { pooling: 'mean', normalize: true })
    return Array.isArray(out) ? out : [out]
  }
}

function ensureLoaded(): Promise<void> {
  if (!loadPromise) {
    loadPromise = loadModel()
  }
  return loadPromise
}

/**
 * Embed a single query string; returns a 384-dim unit vector.
 * Returns null on failure — caller falls back to server-side embedding.
 */
export async function embedQuery(query: string): Promise<number[] | null> {
  try {
    await ensureLoaded()
    if (!pipeline) { console.warn('[embedder] pipeline null after load'); return null }
    const prefixed = `query: ${query}`
    const outputs = await pipeline(prefixed)
    if (!outputs?.[0]) { console.warn('[embedder] empty outputs'); return null }
    const vec = Array.from(outputs[0].data as Float32Array)
    console.log(`[embedder] OK dim=${vec.length} sample=${vec[0].toFixed(4)}`)
    return vec
  } catch (err) {
    console.warn('[embedder] failed — falling back to server-side embedding:', err)
    _fallbackCount++
    if (_fallbackCount % 5 === 1) {
      console.warn(`[embedder] client-side embedding has failed ${_fallbackCount} time(s) this session`)
    }
    return null
  }
}

let _fallbackCount = 0

export const isEmbedderReady = (): boolean => pipeline !== null
