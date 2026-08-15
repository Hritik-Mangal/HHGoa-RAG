import sys, io, asyncio, httpx
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('intfloat/multilingual-e5-small')

queries = [
    'what is photosynthesis',
    'टेल मी व्हाट इज फोटोसिंथेसिस',
    'what is a corporation',
]

async def run():
    async with httpx.AsyncClient(timeout=20) as client:
        for query in queries:
            vec = model.encode(['query: ' + query], normalize_embeddings=True, convert_to_numpy=True)[0].tolist()
            r = await client.post('http://localhost:8001/api/query', json={
                'transcript': query, 'query_vector': vec, 'language': 'hi', 'top_k': 5,
            })
            d = r.json()
            lat = d.get('latencies', {})
            print(f'\nQ: {query}')
            print(f'   guardrail={d.get("guardrail")}  grounded={d.get("grounded")}  gen={round(lat.get("generation_ms") or 0)}ms')
            print(f'   ANSWER: {d.get("answer","")[:180]}')

asyncio.run(run())
