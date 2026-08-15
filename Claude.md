# Claude.md — HH Goa 2026: Voice-Enabled RAG Model

## 1. Project Objective

Build a **voice-enabled Retrieval-Augmented Generation (RAG) system** in which a user speaks a question and the system processes it end to end:

**Voice input → Speech-to-text → Chunking / Retrieval (vector DB) → Answer generation**

The system must be genuinely production-oriented rather than a single prompt-in / text-out prototype.

Source task brief:
- Dataset: `ai4bharat/MSMARCO-XI`
- Speech-to-text: **Sarvam OR ElevenLabs** — choose one.
- The task explicitly requires a thoughtful, non-naive chunking strategy.
- The full pipeline has a **<200 ms latency target**.
- Submit **P50, P70, and P100 latency** measured across a reasonable set of test queries.
- Use a proper orchestration harness with tool calls/retries/structured I/O/error recovery.
- Include guardrails for off-topic, unsafe/inappropriate, hallucinated, or poorly grounded answers.
- Required submission: GitHub repository, live working link, two videos, and the submission form.
- Deadline: **August 22, 2026, 11:59 PM**.
- Task launch: August 13, 2026.

See the supplied task brief for the authoritative requirements.

---

## 2. Non-Negotiable Requirements

### Speech-to-Text
Use exactly one of:
- Sarvam
- ElevenLabs

Keep the STT layer behind a clean interface so it can be replaced without changing the rest of the application.

### Dataset
Use:
`https://huggingface.co/datasets/ai4bharat/MSMARCO-XI`

Do not silently substitute another dataset. If preprocessing is required, document the transformation clearly.

### Chunking / Retrieval
Do **not** use one naive fixed-size chunking strategy.

The implementation should demonstrate actual engineering thought around:
- fixed-size vs semantic splitting
- overlap handling
- metadata-aware splitting where useful
- multiple chunking strategies or an adaptive strategy
- indexing and retrieval trade-offs
- retrieval quality vs latency

The final design should make the chunking decision explicit and measurable.

### Latency
Target:
**< 200 ms end-to-end**

Measure the actual pipeline rather than reporting only the fastest request.

At minimum, capture:
- STT time
- retrieval / vector DB time
- generation time
- orchestration / guardrail overhead
- total end-to-end latency

Report:
- **P50**
- **P70**
- **P100**

Use a reasonable test-query set, not one hand-picked example.

Important:
If real speech recognition or LLM inference makes the strict <200 ms requirement difficult, do not fake or manipulate the measurements. Clearly separate:
1. full user-facing latency, and
2. retrieval/generation pipeline latency,
while documenting exactly what is included in each metric.

### Model Harness
Use structured orchestration around the model.

The application should have explicit handling for:
- tool calls
- retries
- structured input/output
- validation
- timeouts
- transient failures
- malformed model output
- dependency failures
- graceful fallbacks

Avoid a single raw prompt → model → answer implementation.

### Guardrails
The system must know when **not** to answer.

Handle at least:
- off-topic queries
- unsafe / inappropriate inputs
- insufficient retrieval evidence
- hallucination / unsupported claims
- low-confidence retrieval

Answers should be grounded in retrieved context. When evidence is insufficient, return a safe refusal / uncertainty response instead of inventing an answer.

---

## 3. Recommended System Architecture

Use a modular architecture similar to:

```text
                         ┌─────────────────────┐
                         │     User Voice      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Speech-to-Text      │
                         │ Sarvam / ElevenLabs │
                         └──────────┬──────────┘
                                    │ transcript
                                    ▼
                         ┌─────────────────────┐
                         │ Query Validation &  │
                         │ Safety Guardrails    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Query Processing /  │
                         │ Retrieval Router    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                  ┌─────────────────────────────────┐
                  │       Vector DB Retrieval       │
                  │  Multi-strategy / metadata-aware│
                  └───────────────┬─────────────────┘
                                  │ top-k context
                                  ▼
                         ┌─────────────────────┐
                         │ Context Validation  │
                         │ + Grounding Check   │
                         └──────────┬──────────┘
                                    │
                        ┌───────────┴───────────┐
                        │                       │
                 sufficient evidence       insufficient
                        │                       │
                        ▼                       ▼
              ┌──────────────────┐      ┌────────────────┐
              │ Answer Generator │      │ Refusal /      │
              │     (LLM)        │      │ Uncertainty    │
              └────────┬─────────┘      └────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Output Validator │
              │ + Grounding      │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Final User Answer│
              └──────────────────┘
```

Keep modules independently testable.

---

## 4. Suggested Repository Structure

Prefer a clean structure like:

```text
.
├── README.md
├── Claude.md
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
│
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── routes.py
│   │   └── schemas.py
│   │
│   ├── stt/
│   │   ├── base.py
│   │   └── provider.py
│   │
│   ├── ingestion/
│   │   ├── load_dataset.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   └── indexing.py
│   │
│   ├── retrieval/
│   │   ├── retriever.py
│   │   ├── strategies.py
│   │   └── reranker.py
│   │
│   ├── generation/
│   │   ├── prompts.py
│   │   ├── generator.py
│   │   └── validators.py
│   │
│   ├── guardrails/
│   │   ├── safety.py
│   │   ├── relevance.py
│   │   └── grounding.py
│   │
│   ├── orchestration/
│   │   ├── pipeline.py
│   │   ├── retry.py
│   │   └── errors.py
│   │
│   └── monitoring/
│       ├── latency.py
│       └── metrics.py
│
├── scripts/
│   ├── ingest.py
│   ├── benchmark.py
│   └── evaluate.py
│
├── tests/
│   ├── test_chunking.py
│   ├── test_retrieval.py
│   ├── test_guardrails.py
│   └── test_pipeline.py
│
├── data/
│   └── .gitkeep
│
└── docs/
    ├── architecture.md
    ├── latency.md
    └── evaluation.md
```

Adapt this structure to the actual implementation instead of creating unnecessary boilerplate.

---

## 5. Engineering Principles

### Build for measurable performance
Do not optimize by intuition alone.

Benchmark:
- embedding/indexing performance
- retrieval latency
- number of retrieved chunks
- generation latency
- total latency
- cold start vs warm start where relevant

Use warm-up requests before final benchmark reporting when appropriate, but document the methodology.

### Separate offline and online work

**Offline:**
- dataset loading
- cleaning
- chunking
- embedding
- vector index construction
- metadata creation

**Online:**
- STT
- query preprocessing
- retrieval
- answer generation
- guardrails
- response

Never rebuild embeddings or indexes during a user request.

### Keep the index persistent
The application should load an already-built vector index rather than recomputing embeddings on every startup/request.

### Avoid unnecessary network calls
Every external call affects latency. Keep the critical path minimal.

### Fail gracefully
Expected failures should produce controlled responses rather than stack traces.

---

## 6. Chunking Strategy Requirements

Implement and compare more than one meaningful strategy.

A good evaluation can compare examples such as:

### Strategy A — Fixed-size
Baseline using token/character windows with controlled overlap.

### Strategy B — Semantic
Split around semantic boundaries / document structure rather than only character count.

### Strategy C — Metadata-aware
Use available document/query metadata to avoid mixing unrelated information.

### Strategy D — Adaptive / hybrid
Use different chunk sizes or overlap based on document characteristics.

The project should answer:

> Why does the selected strategy improve retrieval quality without violating the latency budget?

Record benchmark results for:
- retrieval latency
- number of chunks
- context length
- retrieval relevance / hit rate
- answer quality
- memory / index size where useful

Do not claim a strategy is better without measurements.

---

## 7. Retrieval Design

The retriever should:
1. embed the user query,
2. search the vector index,
3. return top-k candidate chunks,
4. optionally rerank or filter candidates,
5. pass only useful context to the generator.

Avoid excessively large `k`, because retrieval volume directly affects latency and generation cost.

Store useful metadata with each chunk, such as:
- document identifier
- source
- chunk identifier
- position / ordering
- chunking strategy
- other dataset-supported metadata

Only use metadata that actually exists in the source dataset or is generated deterministically during preprocessing.

---

## 8. Generation Requirements

The generation prompt should enforce:

- answer only from retrieved context
- do not fabricate unsupported facts
- acknowledge insufficient context
- distinguish uncertainty from evidence
- keep the response relevant to the query

Use structured output where practical, for example:

```json
{
  "answer": "string",
  "grounded": true,
  "confidence": 0.0,
  "sources": ["chunk_id_1", "chunk_id_2"]
}
```

Validate model output before returning it to the user.

Do not trust model-generated `grounded=true` blindly. Grounding should also be checked against retrieved evidence.

---

## 9. Guardrail Logic

A practical decision flow:

```text
User Query
   │
   ├── unsafe? ───────────────► refuse
   │
   ├── clearly off-topic? ────► decline / redirect
   │
   ▼
Retrieve context
   │
   ├── weak/no evidence? ─────► say insufficient context
   │
   ▼
Generate answer
   │
   ├── unsupported claims? ───► reject / regenerate / refuse
   │
   ▼
Return grounded answer
```

Avoid endless retries. Use bounded retry counts and timeouts.

---

## 10. Orchestration

Create one explicit pipeline/orchestrator responsible for coordinating:

```text
STT
  ↓
Validation
  ↓
Retrieval
  ↓
Context validation
  ↓
Generation
  ↓
Output validation
```

Recommended properties:
- typed request/response objects
- explicit stage boundaries
- structured logs
- correlation/request IDs
- timeout handling
- bounded retries
- clear exception classes
- deterministic fallbacks where possible

Keep orchestration code separate from provider-specific implementations.

---

## 11. Latency Benchmarking

Create a reproducible benchmark script.

Use a fixed evaluation set of multiple queries and run enough samples to avoid reporting an accidental best case.

At minimum produce:

```text
P50:  xx ms
P70:  xx ms
P100: xx ms
```

Also report useful breakdowns:

```text
STT:          xx ms
Query prep:   xx ms
Retrieval:    xx ms
Generation:   xx ms
Guardrails:   xx ms
Total:        xx ms
```

Make clear whether latency metrics include:
- network time
- STT
- LLM generation
- initialization
- retries
- serialization

Never invent benchmark numbers.

---

## 12. Evaluation

Evaluate both **quality** and **latency**.

### Retrieval metrics
Choose metrics that fit the available ground truth, such as:
- Recall@K
- Hit@K
- MRR / ranking quality where applicable

### Answer metrics
Measure:
- groundedness
- relevance
- refusal correctness
- hallucination rate

### System metrics
Measure:
- P50
- P70
- P100
- error rate
- timeout rate

Document the methodology and dataset split used for evaluation.

---

## 13. API / UI Expectations

Provide a simple live interface suitable for demonstration.

Minimum UX:
1. user provides voice input
2. system transcribes it
3. system retrieves evidence
4. system generates an answer
5. user can see the final response

Expose useful debugging/observability information separately from the user-facing answer, such as:
- transcript
- retrieval latency
- number of retrieved chunks
- total latency
- grounding decision

Do not expose secrets or internal credentials.

---

## 14. Configuration & Secrets

Use environment variables.

Provide:

```text
.env.example
```

Never commit:
- API keys
- access tokens
- private credentials
- local secret files

Configuration should cover:
- STT provider
- model/provider settings
- vector DB path / connection
- retrieval parameters
- timeout values
- retry limits
- logging level

---

## 15. Error Handling

Handle at least:
- STT failure
- empty transcript
- malformed request
- vector DB unavailable
- embedding failure
- generation timeout
- provider rate limit
- model output validation failure
- unsafe input
- insufficient retrieval evidence

Return user-friendly errors while logging enough technical information for debugging.

Never leak stack traces or credentials to the client.

---

## 16. Development Workflow

When modifying the project:

1. Inspect the existing repository before changing architecture.
2. Preserve working components where possible.
3. Implement one concern at a time.
4. Add tests for non-trivial logic.
5. Run formatting/linting/type checks if configured.
6. Run unit tests.
7. Run an end-to-end smoke test.
8. Run latency benchmarks after performance-sensitive changes.
9. Update README/docs when behavior changes.
10. Verify that the Git repository does not contain secrets.

Do not rewrite the entire project simply to introduce a preferred framework.

---

## 17. Definition of Done

The implementation is complete only when:

- [ ] Voice input works end to end.
- [ ] Exactly one supported STT provider is integrated: Sarvam or ElevenLabs.
- [ ] `MSMARCO-XI` is used as the dataset.
- [ ] Chunking is meaningfully more sophisticated than one naive fixed-size splitter.
- [ ] The vector index is built offline and reused online.
- [ ] Retrieval works reliably.
- [ ] The model is run through a structured harness/orchestrator.
- [ ] Retries, timeouts, validation, and error recovery exist.
- [ ] Guardrails handle off-topic inputs.
- [ ] Guardrails handle unsafe/inappropriate inputs.
- [ ] The system avoids answers unsupported by retrieved context.
- [ ] P50/P70/P100 latency are measured across multiple queries.
- [ ] Latency methodology is documented honestly.
- [ ] The live project is demonstrable.
- [ ] GitHub repository is clean and reproducible.
- [ ] README explains setup, architecture, usage, benchmarking, and limitations.
- [ ] Two videos are prepared:
  - [ ] 90-second team/process video
  - [ ] end-to-end demo video
- [ ] Both videos are uploaded by every team member to Instagram, X, and LinkedIn.
- [ ] At least one Instagram account is public.
- [ ] Every required social post includes `#RAGInGoa`.
- [ ] Submission form is completed.
- [ ] Final submission is made before **August 22, 2026, 11:59 PM**.

---

## 18. Claude Code Behavior

When working on this project, Claude should:

### Prioritize
1. Task compliance
2. Correctness
3. Measurable retrieval quality
4. Latency
5. Reliability
6. Clean architecture
7. Demo quality

### Do not
- fabricate benchmark results
- claim the <200 ms target is achieved without measurement
- silently replace the required dataset
- use a single naive chunking method and call it sufficient
- return unsupported answers merely to satisfy the user
- hard-code secrets
- hide errors that should be surfaced
- add unnecessary dependencies without justification
- build an overcomplicated architecture before establishing the working baseline

### Before declaring a feature complete
Check:
- Is it actually implemented?
- Is it tested?
- Does it work end to end?
- Does it affect latency?
- Is the effect measured?
- Is documentation updated?

---

## 19. Final Submission Checklist

Before submission, verify the repository and live deployment manually.

### Product
- [ ] Voice input
- [ ] STT
- [ ] Retrieval
- [ ] Grounded answer
- [ ] Refusal behavior
- [ ] Error recovery

### Engineering
- [ ] Multiple / adaptive chunking strategy
- [ ] Persistent vector index
- [ ] Structured orchestration
- [ ] Guardrails
- [ ] Benchmarking
- [ ] Tests
- [ ] Environment configuration
- [ ] No secrets committed

### Evidence
- [ ] Architecture documented
- [ ] Chunking rationale documented
- [ ] P50/P70/P100 documented
- [ ] Query benchmark methodology documented
- [ ] Known limitations documented

### Submission
- [ ] GitHub repo
- [ ] Live working link
- [ ] 90-sec process video
- [ ] Demo video
- [ ] Videos posted by every team member
- [ ] Instagram + X + LinkedIn
- [ ] At least one public Instagram account
- [ ] `#RAGInGoa` on every post
- [ ] Submission form
- [ ] Submit before deadline

---

# 20. Premium / Royal UI Design System

The application should not look like a generic RAG demo or a standard dashboard. The visual direction is:

> **Royal + Premium + Futuristic + Funky + Intelligent**

Think of a high-end emerald/forest-green private club combined with modern AI product design. The interface should feel expensive, polished, and distinctive without becoming visually noisy.

## 20.1 Design Direction

Use:
- deep green / emerald foundations
- subtle black-green gradients
- muted gold/brass accents
- ivory / warm-white typography
- translucent glass surfaces
- fine grain/noise texture
- soft glows
- elegant borders
- rounded but not childish geometry
- restrained neon accents for AI states

Avoid:
- generic blue SaaS styling
- excessive pure-black backgrounds
- rainbow gradients
- overly bright neon
- excessive rounded cards
- cheap-looking gold/yellow
- stock-dashboard appearance
- excessive shadows
- animations that interfere with usability

The overall visual hierarchy should feel **luxurious first, technical second**.

---

## 20.2 Premium Color Palette

Use these as the primary design tokens:

```css
:root {
  /* Base */
  --bg-primary: #07140F;
  --bg-secondary: #0B1F16;
  --bg-elevated: #102A1E;
  --bg-surface: rgba(16, 42, 30, 0.72);

  /* Royal greens */
  --emerald-950: #032B20;
  --emerald-900: #064B38;
  --emerald-800: #086A4E;
  --emerald-700: #0A8763;
  --emerald-500: #19A974;
  --emerald-300: #5BD6A3;

  /* Luxury accent */
  --gold-500: #C8A55A;
  --gold-400: #D9BA70;
  --gold-300: #E8D19A;

  /* Typography */
  --text-primary: #F5F2E8;
  --text-secondary: #C6D2CA;
  --text-muted: #81978B;

  /* Status */
  --success: #53D68A;
  --warning: #D9B765;
  --danger: #E47C7C;

  /* Borders */
  --border-subtle: rgba(200, 165, 90, 0.18);
  --border-green: rgba(91, 214, 163, 0.18);
}
```

Primary visual gradient:

```css
background:
  radial-gradient(circle at 15% 10%, rgba(25, 169, 116, 0.16), transparent 28%),
  radial-gradient(circle at 85% 80%, rgba(200, 165, 90, 0.10), transparent 26%),
  linear-gradient(135deg, #07140F 0%, #0B1F16 50%, #05100C 100%);
```

Gold should be used as an **accent**, not the dominant color.

---

## 20.3 Greenish Texture

Add a subtle premium texture over large background surfaces.

Recommended implementation:

```css
.app-shell::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  opacity: 0.035;
  background-image:
    radial-gradient(rgba(255,255,255,0.7) 0.5px, transparent 0.5px);
  background-size: 5px 5px;
  mix-blend-mode: soft-light;
}
```

Optionally combine this with:
- very subtle organic noise
- emerald radial light blooms
- faint decorative line patterns

Texture must remain subtle enough that body text remains highly readable.

---

## 20.4 Typography

Use a premium editorial + modern technical pairing.

Preferred:
- Display / headings: **Cormorant Garamond**, **Playfair Display**, or a similar elegant serif.
- Body / UI: **Inter**, **Manrope**, or **DM Sans**.
- Data / technical labels: **JetBrains Mono** or similar monospace.

Suggested hierarchy:

```text
Eyebrow / label     11–12px, uppercase, letter-spacing 0.14em
Display title       48–72px, elegant serif, medium weight
Section heading     28–36px, serif or refined sans
Body                14–17px
UI labels           12–14px, medium weight
Metrics             28–44px, sans/mono
Technical metadata  11–12px, monospace
```

Do not use all-serif typography. Serif should create the royal character while the sans-serif system preserves usability.

---

## 20.5 Logo / Brand Treatment

The product mark should feel like a luxury AI intelligence system.

Recommended visual idea:
- stylized emerald crest / abstract speech-wave emblem
- thin gold outline
- subtle circular geometry
- no cartoon mascot
- no excessive gradients

Logo animation:
- idle: almost imperceptible glow
- listening: slow emerald pulse
- processing: rotating/rippling halo
- answer ready: brief gold shimmer

---

## 20.6 Landing / Hero Experience

The first screen should immediately communicate:

**Voice → Intelligence → Grounded Answer**

Recommended composition:

```text
┌─────────────────────────────────────────────────────┐
│  BRAND                         STATUS / NAV          │
│                                                     │
│             THE VOICE OF KNOWLEDGE                  │
│       Ask naturally. Discover precisely.             │
│                                                     │
│             [  ◉ HOLD TO SPEAK  ]                   │
│                                                     │
│       waveform / orbital listening animation        │
│                                                     │
│     Grounded retrieval  •  Fast inference            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

Use generous whitespace and visual depth.

The microphone / voice control should be the primary interaction, not a conventional text input.

---

## 20.7 Core Components

Create a reusable component system.

### VoiceOrb

The central voice interaction component.

States:

```text
idle
hover
listening
transcribing
retrieving
generating
complete
error
```

Visual behavior:
- idle: glass orb with faint emerald core
- hover: gold rim illuminates
- listening: waveform/ripple expands
- retrieving: emerald particles orbit the orb
- generating: subtle rotating ring
- complete: short gold pulse
- error: restrained red pulse

Do not overuse particle effects.

---

### Waveform

Use a dynamic waveform around or beneath the VoiceOrb.

Characteristics:
- thin emerald lines
- occasional gold highlights
- responsive to input volume where available
- smooth interpolation rather than abrupt bar changes

The waveform should feel musical and premium.

---

### GlassPanel

Shared container for:
- transcript
- retrieved sources
- answer
- metrics
- system state

Style:

```css
background: rgba(16, 42, 30, 0.62);
border: 1px solid rgba(200, 165, 90, 0.14);
backdrop-filter: blur(18px);
border-radius: 20px;
box-shadow:
  0 20px 70px rgba(0,0,0,0.24),
  inset 0 1px 0 rgba(255,255,255,0.035);
```

Use shallow depth rather than heavy floating cards.

---

### AnswerCard

The final answer should receive the strongest content hierarchy.

Structure:

```text
ANSWER
────────────────────────
Answer text...

Grounded in 4 retrieved passages
Confidence: High
```

Include:
- concise answer
- source/chunk indicators
- grounding status
- confidence/reliability indicator where implemented

A successful grounded answer can use a subtle emerald edge glow.

---

### SourceCard

Display retrieved evidence elegantly.

Include:
- source identifier
- relevant excerpt
- retrieval score if meaningful
- chunk metadata
- expandable detail

Use a slim left accent line rather than a large colored card.

---

### MetricPill

For:
- P50
- P70
- P100
- retrieval latency
- generation latency
- grounding status

Use compact pill/chip components with monospace values.

---

### SystemStatus

Show current pipeline state:

```text
LISTENING
TRANSCRIBING
RETRIEVING
GENERATING
GROUNDED
```

Each state should have a subtle animated indicator.

---

## 20.8 Motion System

Animations should feel **royal and funky**, but still sophisticated.

Use:
- spring-based transitions
- slow ambient motion
- subtle glow
- orbital movement
- line-drawing effects
- waveform motion
- staggered content reveal

Avoid:
- constant bouncing
- excessive scaling
- spinning entire UI components
- fast flashing
- animations longer than necessary

Suggested timing:

```text
micro interaction: 120–180ms
panel transition: 220–350ms
content reveal: 350–600ms
ambient animation: 4–12s
hero motion: 8–20s
```

Use easing similar to:

```css
cubic-bezier(0.22, 1, 0.36, 1)
```

---

## 20.9 Signature Animations

### Royal Pulse

A slow emerald/gold pulse around the voice orb.

```text
core glow → ring expands → fades → second ring → repeat
```

Cycle approximately every 4–6 seconds while idle.

### Listening Ripple

When recording:

```text
voice input
   ↓
central orb
   ↓
3–5 expanding rings
   ↓
rings fade into background
```

The ring speed should correlate loosely with audio energy.

### Retrieval Orbit

During vector retrieval, use 2–4 small luminous nodes moving around the central orb.

This visually communicates:
**query → search → context**

### Answer Reveal

Do not simply pop the answer card in.

Use:

```text
panel fades in
→ border illuminates
→ answer text rises 6–10px
→ supporting sources reveal sequentially
```

### Gold Shimmer

Use sparingly for major successful states.

A narrow gold highlight can travel across the border of the final grounded-answer card once.

---

## 20.10 Page Transitions

Use subtle transitions between:
- home
- live query
- results
- system analytics

Prefer:
- opacity
- blur
- vertical translation
- masked reveals

Avoid dramatic page rotations or 3D flips.

---

## 20.11 Interactive States

Every interactive component needs:

### Default
Clean, calm, premium.

### Hover
- slight brightness increase
- gold/emerald border activation
- 1–2px elevation shift

### Active
- compressed 1–2px
- stronger inner glow

### Focus
Visible keyboard-accessible focus ring using emerald/gold.

### Disabled
Reduced opacity but still readable.

### Error
Use muted red rather than saturated emergency red.

---

## 20.12 Dashboard / Analytics View

The analytics page should feel like a private intelligence console rather than a generic admin dashboard.

Recommended layout:

```text
┌───────────────────────────────────────────────────┐
│ PIPELINE PERFORMANCE                              │
│                                                   │
│  P50       P70       P100       SUCCESS RATE      │
│  84ms      112ms     171ms      98.7%             │
│                                                   │
├───────────────────────────────────────────────────┤
│ RETRIEVAL PERFORMANCE                             │
│                                                   │
│  latency chart / query distribution               │
│                                                   │
├───────────────────────────────────────────────────┤
│ PIPELINE BREAKDOWN                                │
│                                                   │
│ STT → RETRIEVAL → GENERATION → GUARDRAILS         │
└───────────────────────────────────────────────────┘
```

Use charts sparingly. The page should remain elegant.

---

## 20.13 Background Effects

Recommended ambient effects:
- slow emerald light bloom
- faint gold halo around active elements
- subtle grain
- very slow floating particles
- faint radial gradients

Particles must never reduce legibility.

Respect:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 20.14 Responsive Design

Desktop is the primary demo environment, but mobile/tablet must remain functional.

### Desktop
- cinematic hero
- large VoiceOrb
- multi-column evidence/results layout

### Tablet
- reduced hero scale
- two-column where possible

### Mobile
- single-column
- VoiceOrb remains dominant
- source cards become expandable
- metrics become horizontal scroll/chips
- avoid tiny text

Never allow decoration to consume the interaction area on small screens.

---

## 20.15 Accessibility

Premium styling must not compromise usability.

Ensure:
- WCAG-conscious contrast
- keyboard navigation
- visible focus states
- semantic HTML
- screen-reader labels for voice controls
- clear error messages
- reduced-motion support
- no information conveyed solely through color

The microphone button must have an accessible label such as:

```text
"Hold to speak"
```

State changes should be exposed programmatically where appropriate.

---

## 20.16 Sound Design (Optional, Use Sparingly)

If sound is implemented, keep it extremely subtle.

Possible sounds:
- soft chime when recording begins
- low-frequency confirmation when retrieval completes
- delicate tonal cue when final answer is ready

Do not autoplay sound without a user interaction.

Allow mute/disable.

---

## 20.17 Component Naming

Use clear reusable names such as:

```text
AppShell
RoyalHeader
VoiceOrb
WaveformVisualizer
PipelineStatus
GlassPanel
TranscriptPanel
SourceCard
AnswerCard
GroundingBadge
MetricPill
LatencyChart
ErrorToast
Footer
```

Avoid page-specific duplicated components when a reusable primitive would work.

---

## 20.18 Frontend Quality Bar

The final interface should look like a product that could be shown in a premium AI product launch—not a university assignment.

Before declaring the UI complete, verify:

- [ ] Visual identity is consistently emerald + deep green + restrained gold.
- [ ] Background has a subtle greenish texture.
- [ ] Typography has a clear editorial hierarchy.
- [ ] Voice interaction is visually dominant.
- [ ] Listening/retrieval/generation states are animated.
- [ ] Answer and evidence hierarchy is clear.
- [ ] Analytics use the same design language.
- [ ] Motion feels smooth and intentional.
- [ ] No animation is distracting.
- [ ] Responsive layouts work.
- [ ] Reduced-motion mode works.
- [ ] Keyboard accessibility works.
- [ ] Loading, empty, success, and error states are designed.
- [ ] No component looks like an untouched default library component.

---

## 20.19 Implementation Rule for Claude

When implementing the UI, do not merely apply the color palette to a generic template.

Build the visual system intentionally:
1. establish design tokens,
2. establish typography,
3. establish the background/texture layer,
4. build the VoiceOrb interaction,
5. build the glass panel primitives,
6. build answer/source/metric components,
7. add state-based motion,
8. add responsive behavior,
9. add accessibility,
10. polish spacing, shadows, borders, and micro-interactions.

The final result should communicate **premium intelligence, royal elegance, and modern AI energy** at first glance.

