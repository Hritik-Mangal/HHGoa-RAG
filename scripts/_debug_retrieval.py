import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv()
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('intfloat/multilingual-e5-small')
query = 'what is photosynthesis'
vec = model.encode(['query: ' + query], normalize_embeddings=True, convert_to_numpy=True)[0]

vectors = np.load('api/artifacts/vectors.npy').astype(np.float32)
scores = vectors @ vec
top_idx = np.argsort(scores)[::-1][:5]

with open('api/artifacts/metadata.json', encoding='utf-8') as f:
    metadata = json.load(f)

threshold = float(os.getenv('SIM_THRESHOLD', '0.45'))
print(f'SIM_THRESHOLD = {threshold}')
print()
for i, idx in enumerate(top_idx):
    score = float(scores[idx])
    text = metadata[idx]['text'][:120]
    passes = 'PASS' if score >= threshold else 'BLOCKED'
    print(f'#{i+1} [{passes}] score={score:.4f}  {text}')
