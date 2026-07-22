# RAG Implementation Plan — ResilienceAI

> **Status**: Planning document, read-only. No code has been written.
> **Date authored**: July 20, 2026
> **Project**: `ResilienceAI` (Myanmar Youth AI Innovation Competition 2026)
> **Author**: Planning/research task delegated to AI assistant (read-only inspection only)

---

## 1. Summary of Existing Project Architecture

After inspecting the codebase (backend at `D:\Work\Projects\ResillienceAI\backend\`), the system is a FastAPI application with a clean separation of concerns across four routers:

| File | Role |
|---|---|
| `main.py` | App factory, lifespan that loads `seismic_resilience_xgb.pkl` + `model_features.json` from `backend/models/` into `app.state` |
| `routes/resilience.py` | `POST /api/resilience/assess` — runs the XGBoost model and returns a 0–100 resilience score + `building_llm_context` |
| `routes/hazard.py` | `POST /api/hazard/calculate` — runs the hazard engine for a coordinate and returns a `HazardReport` including `environmental_context` |
| `routes/llm.py` | `POST /api/llm/analysis` — thin wrapper around `LLMService.analyze(input)` |
| `routes/assessment.py` | `POST /api/assessment/process` — **the orchestrator** (SSE streamed). Runs resilience + hazard in parallel, then calls LLM, then persists to Neon Postgres |
| `services/pipeline.py` | `StructuralFeatureExtractor` (sklearn transformer), `process_and_align_inference_data` (train/inference schema alignment) |
| `services/resilience_engine.py` | Maps `predict_proba` → 0–100 resilience score via `(P_low * 100) + (P_med * 45)` |
| `services/llm_services.py` | `GenAIClient` (Gemini 2.5 Flash, 3-retry exponential backoff, schema cleaning) + `LLMService.analyze()` with strict 6-bullet / 5-recommendation prompt |
| `services/hazard_engine/` | Location → seismic/soil/fault analysis → `EnvironmentalContext` (Pydantic) |
| `richtor_mappings.py` | **Already contains authoritative vulnerability descriptions** for foundation, roof, ground floor types (R/I/U/W/H for foundation; N/Q/X for roof; F/V/X/M/Z for floor) |
| `project_schema.py` | All Pydantic models, including the LLM response contract |

The existing LLM response contract (from `project_schema.py`) is:

```python
class LLMRecommendation(BaseModel):
    priority: str  # "red" | "yellow" | "blue"  (NB: prompt uses 4 colors, schema says 3 — minor inconsistency)
    title: str
    description: str

class LLMAnalysisOutput(BaseModel):
    summary: List[str]              # exactly 6 bullets (per prompt)
    recommendations: List[LLMRecommendation]  # exactly 5 items (per prompt)
    risk_interpretation: Dict[str, Any]
    confidence: float
```

**The RAG system must preserve this contract exactly.**

---

## 2. Current LLM Data Flow

Traced from `routes/assessment.py:process_assessment()`:

```
[POST /api/assessment/process  — payload = AssessmentRequest (lat, lon, 11 building fields)]
        │
        ▼
[SSE stage_started: "initializing"]
        │
        ├── build HazardInput(lat, lon, search_radius_km=100, historical_years=50, min_mag=4.5)
        ├── build BuildingInput(11 building fields)
        │
[SSE stage_completed: "initializing"]
        │
[SSE stage_started: "resilience"] + [SSE stage_started: "hazard"]  (parallel)
        │
        ├── asyncio.to_thread(calculate_pure_resilience, payload, request)
        │       └─ predict_resilience() → ResilienceAssessmentResponse
        │             • runs process_and_align_inference_data
        │             • runs calculate_resilience_score
        │             • builds BuildingLLMContext (structural / material / substructure dicts)
        │
        └── asyncio.create_task(calculate_hazard_route(inputs))
                └─ calculate_hazard_pydantic() → HazardReport
                      • events list (USGS), faults, soil, ground motion
                      • builds EnvironmentalContext (hazard_score, hazard_level,
                        historical_activity, faults, soil, ground_motion, summary[])
        │
        await asyncio.gather(building_task, hazard_task)
        │
[SSE stage_completed: "resilience"] + [SSE stage_completed: "hazard"]
        │
[SSE stage_started: "llm"]
        │
        ├── building_json["building_llm_context"] + hazard_json["environmental_context"]
        │   → LLMAnalysisInput
        │
        ├── asyncio.to_thread(llm_service.analyze, llm_input)
        │       └─ LLMService.analyze():
        │             • _build_prompt(building_context, environmental_context)
        │             • self.client.generate(prompt, schema=LLMAnalysisOutput.model_json_schema())
        │                 └─ GenAIClient.generate():
        │                       • clean_schema() (strips additionalProperties)
        │                       • 3-retry exponential backoff (2^n + jitter)
        │                       • safe_json_load() on response text
        │             • return LLMAnalysisOutput(**result)
        │
[SSE stage_completed: "llm"]
        │
[SSE stage_started: "saving"]
        ├── save_assessment(profile, building, hazard, llm) → Neon Postgres
[SSE stage_completed: "saving"]
        │
[SSE type: "complete" — assessment_id]
```

**Critical observation for RAG design**: the LLM call is the only sequential blocking step after the parallel pair. It's also wrapped in `asyncio.to_thread` because Gemini is synchronous. **This is exactly the right place to insert retrieval** — it adds latency, but the user is already in the "AI feedback" loading stage, so a 200–500 ms retrieval cost is invisible.

The two pieces of context passed to the prompt today (`BuildingLLMContext` and `EnvironmentalContext`) are already structured. Retrieval can be **conditioned on fields in these two structures** — we don't need a free-form query.

---

## 3. Recommended RAG Architecture

### Recommendation in one sentence

> **Markdown knowledge chunks → ChromaDB (persistent, embedded) → `all-MiniLM-L6-v2` embeddings (local, free) → hybrid BM25 + semantic top-k=4 retrieval → injected into the existing prompt between the assessment context and the strict output rules → LLM contract preserved unchanged.**

### Why this specific stack (and what was rejected)

| Layer | Choice | Why this, not the alternatives |
|---|---|---|
| **Knowledge format** | Markdown files in `backend/data/knowledge/` (one file per topic) | Authored by hand, easy to inspect, easy to extend, no DB lock-in. JSON would work but is harder to read; SQLite is overkill at this scale (50–200 chunks expected). |
| **Vector store** | **ChromaDB** (persistent, embedded client) | Zero-config, runs in-process (no separate server), persistent on disk (`backend/data/chroma/`), Python-native API matches the existing stack. FAISS rejected — no metadata filtering, no persistence out-of-the-box, more code to manage. Pinecone/Qdrant rejected — require network accounts, fail in Myanmar, contradict the "low complexity / easy deployment" goal. |
| **Embedding model** | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim, ~80 MB on disk, runs on CPU in <50 ms per query, MIT licensed, the de-facto standard for small RAG. bge-small rejected (slightly better quality, but heavier and unnecessary at this scale). API embeddings rejected — would add a new paid external dependency and a new failure mode (rate limits, network, VPN). |
| **Retrieval** | **Hybrid: BM25 keyword + cosine semantic, fused with Reciprocal Rank Fusion (RRF), top-k=4** | Pure semantic loses exact technical terms (e.g. "soft story", "punching shear"). Pure BM25 misses paraphrased context. Hybrid is the modern default. RRF is one of the cleanest fusion methods — no score normalization needed. |
| **LLM integration** | Prepend a `RETRIEVED KNOWLEDGE` section to the existing prompt, between the assessment context and the output rules. | Preserves the existing `_build_prompt()` and response contract exactly. No new LLM code needed. |
| **Citations in output** | **No** — not in the LLM's structured output, but **stored server-side** for the frontend to optionally display later. | Adding a `citations` field to `LLMAnalysisOutput` would break the existing contract. Citations are useful but optional — keep them out of v1. |

### Cost analysis

- **Embeddings**: $0 (local model, runs once at startup to build the index; queries are CPU inference in <50 ms)
- **Vector store**: $0 (ChromaDB runs in-process, data on local disk)
- **Retrieval**: $0 (BM25 is `rank_bm25` pure Python, semantic is the same model)
- **Storage**: <50 MB total (knowledge MD files + Chroma SQLite + embedding model cache)
- **Latency added per assessment**: ~300–500 ms (1× query embedding + BM25 + fusion), well under the user's perception threshold during the LLM loading stage

---

## 4. Recommended Technology Choices (and alternatives kept in reserve)

```text
PRIMARY STACK:
  chromadb            # vector store with metadata filtering
  sentence-transformers  # local embeddings
  rank_bm25           # BM25 keyword retrieval
  tiktoken            # token counting for context budget
  (no other new deps)

REJECTED ALTERNATIVES:
  faiss               # too low-level; no metadata, no persistence
  lancedb             # good but adds a new DB engine
  pinecone / qdrant   # require network accounts, fail offline/in-Myanmar
  openai embeddings   # costs money, adds VPN dependency
  langchain           # massive dep, overkill for 4-file RAG
  llama-index         # same as langchain
```

**Why "no LangChain / no LlamaIndex"**: both add hundreds of MB of dependencies for what is essentially 4 well-defined operations (load chunks, embed, retrieve, format). Hand-rolled RAG at this scale is ~150 lines.

---

## 5. Knowledge Base Design

### What goes in the KB

Five categories, with target sizes:

| Category | Target chunks | Primary purpose |
|---|---|---|
| `earthquake_safety/` | 8–12 | Before/during/after advice to appear in `summary[]` and `recommendations[]` |
| `building_vulnerability/` | 20–30 | Material/age/floors/soft-story explanations to ground structural reasoning |
| `mitigation/` | 10–15 | Retrofits, strengthening, maintenance for the recommendations |
| `environmental/` | 6–10 | Soil amplification, fault proximity, historical seismicity explanations |
| `local_context/` | 4–8 | **Myanmar-specific** — Sagaing fault, Mandalay seismic zone, Yangon soft soils, Myanmar National Building Code |

**Total target**: ~50–75 chunks. Each chunk: 100–400 words. A chunk is one topic, not a page.

### File structure

```text
backend/
├── data/
│   └── knowledge/
│       ├── earthquake_safety/
│       │   ├── before.md
│       │   ├── during.md
│       │   ├── after.md
│       │   └── aftershocks.md
│       ├── building_vulnerability/
│       │   ├── materials_overview.md
│       │   ├── mud_mortar_stone.md
│       │   ├── rc_engineered.md
│       │   ├── timber.md
│       │   ├── adobe_mud.md
│       │   ├── soft_story.md
│       │   ├── plan_irregularity.md
│       │   ├── age_fatigue.md
│       │   ├── height_to_floor_ratio.md
│       │   └── foundation_types.md
│       ├── mitigation/
│       │   ├── retrofitting_overview.md
│       │   ├── wall_anchoring.md
│       │   ├── roof_bracing.md
│       │   ├── column_strengthening.md
│       │   └── maintenance.md
│       ├── environmental/
│       │   ├── soil_amplification.md
│       │   ├── liquefaction.md
│       │   ├── fault_proximity.md
│       │   └── historical_seismicity.md
│       └── local_context/
│           ├── myanmar_overview.md
│           ├── sagaing_fault.md
│           ├── yangon_soft_soil.md
│           └── myanmar_building_code.md
```

### Frontmatter schema (required on every chunk)

```markdown
---
id: "vuln-mud-mortar-stone"
category: "building_vulnerability"
tags: ["material", "mud_mortar_stone", "high_vulnerability", "nepal_context"]
applies_when:
  material_codes: ["mud_mortar_stone"]
  min_age: 0
source:
  name: "Nepal Earthquake 2015 Post-Disaster Building Damage Survey"
  type: "academic_survey"
  url: "https://..."
  license: "CC-BY-4.0"
  retrieved: "2026-07-20"
---

# Vulnerability of Mud Mortar Stone Construction

Mud mortar stone buildings showed near-total collapse rates above MMI VIII...
```

The `applies_when` block enables metadata-filtered retrieval (see Phase 4). `source` enables citation tracking.

### Source evaluation

| Source | Type | Reliability | Include? | Why |
|---|---|---|---|---|
| **GEM Taxonomy / GEM Building Taxonomy** | Academic, global standard | High | ✅ Yes | This is what the Richter dataset itself uses for its damage labels — keeping the KB aligned is non-negotiable. |
| **FEMA P-154 (Rapid Visual Screening)** | Government guidance (US) | High | ✅ Yes | Free, authoritative, applicable globally with adaptation. |
| **USGS Earthquake Hazards Program** | Government | Very high | ✅ Yes | Already implicit in the hazard engine's USGS data; the KB lets the LLM cite what the data means. |
| **ATC-20 (Post-earthquake safety evaluation)** | Engineering standard | High | ✅ Yes | Underpins "what to do after" advice. |
| **Myanmar National Building Code (if publicly available)** | Government (Myanmar) | High if available | ⚠️ Conditional | Often restricted; check before authoring. If not available, use the older UN-Habitat Myanmar profile. |
| **UN-Habitat Myanmar country profile** | International org | Medium-high | ✅ Yes | Open, free, contextual. |
| **Earthquake Engineering Research Institute (EERI) case studies** | Professional society | High | ✅ Yes | For Sagaing fault + Myanmar context. |
| **Myanmar Engineering Council publications** | Professional | Medium | ⚠️ Conditional | Check accessibility. |
| **OpenAI/Anthropic safety guides for earthquakes** | General | Medium | ✅ Yes, but only for the "during earthquake" advice | Supplement, not primary. |
| **Generic AI-generated blog posts** | — | Low | ❌ No | Explicitly excluded — defeats the purpose of RAG grounding. |

### Myanmar-specific sources (highest priority to add)

1. **Sagaing Fault profile** — 1,400 km strike-slip fault running through central Myanmar; source of the 2025 M7.7 earthquake
2. **Yangon soft soil amplification** — Yangon sits on deep alluvial deposits; well-documented amplification risk
3. **Mandalay seismic zone** — historic M8.0 1839 earthquake; modern building stock largely non-engineered
4. **Myanmar National Building Code (2016, 2019 updates)** — if publicly accessible

---

## 6. Retrieval Strategy

### Query construction (deterministic, not free-form)

The query is **built from the structured assessment**, not from a user prompt. This is the key design decision — it prevents irrelevant retrieval and keeps latency predictable.

```python
def build_retrieval_query(building_ctx, env_ctx) -> list[dict]:
    """
    Returns a list of {query: str, filter: dict, k: int} entries,
    one per retrieval 'channel'. Each channel is independent.
    """
    return [
        # Channel 1: vulnerability-specific (1-2 chunks)
        {
            "query": _material_query(building_ctx) + " " + _structural_query(building_ctx),
            "filter": {"category": {"$in": ["building_vulnerability", "mitigation"]}},
            "tags_filter": _tag_filter_for_building(building_ctx),
            "k": 2,
        },
        # Channel 2: environmental-specific (1-2 chunks)
        {
            "query": _env_query(env_ctx),
            "filter": {"category": "environmental"},
            "k": 2,
        },
        # Channel 3: Myanmar local context (always 1 chunk, if available)
        {
            "query": f"Myanmar earthquake risk {env_ctx.summary[0] if env_ctx.summary else ''}",
            "filter": {"category": "local_context"},
            "k": 1,
        },
    ]
```

**Why per-channel retrieval, not one big query**: different assessment fields (vulnerability vs. environment) match different KB categories. A single combined query dilutes relevance. Per-channel retrieval with smaller `k` per channel gives **more relevant total chunks** than one big query with `k=6`.

### Hybrid fusion (per channel)

```text
BM25 top-20  ──┐
                ├── Reciprocal Rank Fusion (RRF, k=60) ── top-k=2 per channel
Semantic top-20 ──┘
```

RRF is cheap, no score normalization needed, well-documented in the literature I cited earlier.

### Total retrieval budget

- 2 (vulnerability) + 2 (environmental) + 1 (local) = **5 chunks max**
- Each chunk truncated to ~500 tokens
- Total injected context: **~2,500 tokens** — leaves Gemini's 1M-token context window with massive headroom, well under any rate limit

### How to prevent irrelevant information

1. **Metadata filters** (`applies_when` in the chunk frontmatter) — e.g. a chunk tagged `material_codes: ["mud_mortar_stone"]` only retrieves for buildings with that material
2. **Hard ceiling on `k` per channel** — prevents one channel from dominating
3. **Token-budget truncation** — if total retrieved > budget, drop lowest-ranked chunks
4. **Empty-context path is well-defined** — if all channels return empty, prompt is built with `RETRIEVED KNOWLEDGE: (none)` (see Phase 6)

### What should NOT be retrieved

- Long pages or full PDFs (chunks should be self-contained)
- The user's own past assessments (privacy; not in scope for v1)
- Code documentation (the LLM doesn't need it)
- Anything tagged `draft: true`

---

## 7. LLM Integration Plan

### Minimal-change principle

The plan modifies **one function** in `llm_services.py` and **one call site** in `routes/assessment.py`. Nothing else changes.

### Modified function in `llm_services.py`

```python
class LLMService:
    def __init__(self, client, retriever=None):  # NEW: retriever is optional
        self.client = client
        self.retriever = retriever  # NEW

    def analyze(self, input_data):
        prompt = self._build_prompt(
            building=input_data.building_context,
            env=input_data.environmental_context,
        )

        # NEW: retrieval is optional and failure-isolated
        if self.retriever is not None:
            try:
                retrieved = self.retriever.retrieve(
                    input_data.building_context,
                    input_data.environmental_context,
                )
            except Exception as e:
                logger.warning(f"Retrieval failed, continuing without: {e}")
                retrieved = []
        else:
            retrieved = []

        prompt = self._inject_retrieved_knowledge(prompt, retrieved)  # NEW

        schema = LLMAnalysisOutput.model_json_schema()
        result = self.client.generate(prompt, schema=schema)
        return LLMAnalysisOutput(**result)

    # NEW: pure formatting, no I/O
    @staticmethod
    def _inject_retrieved_knowledge(prompt: str, retrieved: list) -> str:
        if not retrieved:
            return prompt.replace(
                "RETRIEVED KNOWLEDGE:",
                "RETRIEVED KNOWLEDGE: (none available — rely on your engineering knowledge)"
            )
        chunks = "\n\n---\n\n".join(r["text"] for r in retrieved)
        return prompt.replace("RETRIEVED KNOWLEDGE:", f"RETRIEVED KNOWLEDGE:\n\n{chunks}\n")
```

### Single-line change to the existing prompt template

Insert this block once, between `ENVIRONMENTAL CONTEXT:` and `OUTPUT REQUIREMENTS:`:

```text
-----------------------------
RETRIEVED KNOWLEDGE:
{{retrieved_chunks}}

- Use the above authoritative knowledge to ground your assessment.
- Do NOT invent facts that are not in the assessment or retrieved knowledge.
- If retrieved knowledge is empty, fall back to your engineering training.
-----------------------------
```

**The existing `OUTPUT REQUIREMENTS` block is unchanged. The response contract (`LLMAnalysisOutput`) is unchanged.**

### Modified call site in `routes/assessment.py`

```python
# Was: llm_service = create_llm_service()  (in routes/llm.py, module level)
# New: llm_service = create_llm_service(retriever=build_default_retriever())
```

This is the **only** change at the route level. The orchestrator (`process_assessment`) calls `llm_service.analyze(llm_input)` exactly as it does today.

### Optional: per-assessment citation storage

If you want to expose citations later without breaking the LLM contract, add a server-side log:

```python
# In llm_service.analyze(), after retrieval:
assessment_logger.log_retrieval(
    assessment_id=...,  # passed through context
    retrieved_chunks=[r["id"] for r in retrieved],
)
```

The frontend can later show a "Sources" panel by reading this log. **Not in v1 scope.**

---

## 8. Failure and Fallback Strategy

The RAG system must never break the existing pipeline. Every failure mode has a defined fallback:

| Failure | Detection | Fallback | User-facing effect |
|---|---|---|---|
| **Vector DB missing/corrupt at boot** | Chroma collection doesn't exist on `app.state` init | `retriever = None`; `LLMService` runs without retrieval | Identical to today's behavior |
| **Embedding model fails to load** (network/disk) | Exception during `SentenceTransformer(...)` construction in `lifespan` | Log warning, set `retriever = None` | Identical to today |
| **No relevant results** for a query | All channels return `[]` | Prompt is built with `(none available — rely on your engineering knowledge)` | LLM uses Gemini's training data; works the same as today |
| **LLM API failure** | Already handled by existing 3-retry + 500-error path | Unchanged | Unchanged |
| **Retrieved context too large** | Total tokens > 2,500 budget | Truncate to budget by dropping lowest-ranked chunks | LLM sees slightly less context; still works |
| **Malformed chunk in KB** | YAML parse error on a single file | Skip that file, log warning, continue with rest | KB has one fewer chunk; otherwise fine |
| **Retrieval slow** (>3 s) | Timeout in `asyncio.to_thread` wrapper | Log warning, proceed without retrieval | User sees no LLM delay change; one less grounding pass |
| **KB directory empty** | Zero `.md` files at startup | `retriever = None`; same as first row | Identical to today |
| **Concurrent chunk writes** (in case of a future reindex endpoint) | Chroma handles this internally; use `chromadb.PersistentClient` | n/a | n/a |

**Golden rule**: the entire retrieval subsystem can disappear at any moment and the assessment pipeline continues to work exactly as it does today. This is enforced by (a) the `retriever is None` branch in `LLMService.analyze`, (b) the `try/except` around `retriever.retrieve()`, and (c) the early decision to make retrieval a constructor argument, not a global import.

---

## 9. Proposed File Structure

```text
backend/
├── data/
│   ├── knowledge/                          # NEW: hand-authored KB
│   │   ├── earthquake_safety/*.md
│   │   ├── building_vulnerability/*.md
│   │   ├── mitigation/*.md
│   │   ├── environmental/*.md
│   │   └── local_context/*.md
│   └── chroma/                             # NEW: persistent vector index (auto-created)
│       └── (Chroma SQLite + index files)
│
├── services/
│   ├── (existing files unchanged)
│   ├── retrieval/                          # NEW
│   │   ├── __init__.py
│   │   ├── chunk_loader.py                 # walks data/knowledge/, parses frontmatter
│   │   ├── embedder.py                     # wraps sentence-transformers
│   │   ├── bm25_index.py                   # in-memory BM25 over chunks
│   │   ├── retriever.py                    # hybrid fusion + per-channel query
│   │   └── query_builder.py                # builds per-channel queries from assessment
│
├── tests/
│   ├── (existing files unchanged)
│   ├── test_chunk_loader.py                # NEW
│   ├── test_retriever.py                   # NEW
│   └── test_rag_integration.py             # NEW: end-to-end with mock LLM
│
└── (everything else unchanged)
```

**Zero changes** to: `routes/`, `database/`, `models/`, `main.py` (except 3 lines in the lifespan to load the retriever), `project_schema.py`, existing LLM prompt, existing LLM response contract.

---

## 10. Dependency Changes

### `requirements.txt` — add these three lines

```text
chromadb>=0.5.0
sentence-transformers>=3.0.0
rank-bm25>=0.2.2
```

### Size impact

- `chromadb`: ~50 MB (includes sqlite, no native server)
- `sentence-transformers`: ~3 MB base + auto-downloads `all-MiniLM-L6-v2` (~80 MB on first run, cached in `~/.cache/huggingface/`)
- `rank-bm25`: <1 MB (pure Python)

**Total disk**: ~130 MB. **Total install time**: 2–4 minutes.

### Offline-first design

The embedding model is **downloaded once** on first use, then cached. For competition deployment in Myanmar, this is fine because:
- The cache persists between runs
- If the cache is pre-shipped (e.g. on a USB), it works fully offline after that
- Worst case, retriever fails to load → fallback kicks in (Phase 8) → system works as before

---

## 11. Step-by-Step Implementation Plan

### Phase A — Knowledge Base Creation

| | |
|---|---|
| **Files created** | `backend/data/knowledge/**/*.md` (~50–75 files) |
| **Main work** | Author MD files with frontmatter. Start with `local_context/` (highest leverage for competition) and `building_vulnerability/materials_overview.md` (grounded in your existing `richtor_mappings.py`). |
| **Dependencies** | None |
| **Data flow** | Manual authoring |
| **Testing** | Manual review; each file should be readable in <2 min and self-contained |
| **Risk** | Slow — this is the bulk of the human effort (8–15 hours of writing for a complete KB). **Start with 10–15 high-priority chunks; the system works with any non-empty KB.** |
| **Owner** | You (the model cannot author authoritative earthquake engineering content reliably) |

### Phase B — Embedding / Index Generation

| | |
|---|---|
| **Files created** | `backend/services/retrieval/chunk_loader.py`, `backend/services/retrieval/embedder.py` |
| **Main classes** | `KnowledgeChunk` (dataclass with id, text, metadata), `ChunkLoader.load_all() -> list[KnowledgeChunk]`, `Embedder.embed(texts: list[str]) -> np.ndarray` |
| **Dependencies** | `chromadb`, `sentence-transformers` |
| **Data flow** | `ChunkLoader` → list of chunks → `Embedder` (one batch call) → `chromadb.PersistentClient.get_or_create_collection()` upsert |
| **Testing** | `tests/test_chunk_loader.py` — every MD in `data/knowledge/` parses; frontmatter is valid; no duplicates by `id` |
| **Risk** | First-run model download (mitigated by HF cache); Chroma schema migration if you upgrade (mitigated by pinning `chromadb>=0.5,<1.0`) |

### Phase C — Retrieval Service

| | |
|---|---|
| **Files created** | `backend/services/retrieval/bm25_index.py`, `backend/services/retrieval/query_builder.py`, `backend/services/retrieval/retriever.py` |
| **Main classes** | `BM25Index` (in-memory, rebuilt at boot from chunk texts), `QueryBuilder.build(building_ctx, env_ctx) -> list[ChannelQuery]`, `Retriever.retrieve(building_ctx, env_ctx) -> list[RetrievalResult]` |
| **Dependencies** | `rank_bm25` (BM25), the embedder from Phase B, Chroma collection from Phase B |
| **Data flow** | `Retriever.retrieve(ctx)` → `QueryBuilder` produces 3 channel queries → for each channel: embed query → `chroma.query()` + `bm25.search()` → RRF fuse → take top-k → return list of `RetrievalResult(text, id, score, metadata)` |
| **Testing** | `tests/test_retriever.py` — given a mock building with mud_mortar_stone foundation, top-1 result must be the mud_mortar_stone chunk; given a high-magnitude event, top environmental chunk must mention fault/ground motion |
| **Risk** | Cold-start latency on first call (BM25 index + embedding model load) — mitigated by doing this in `lifespan` startup, not on first request |

### Phase D — LLM Integration

| | |
|---|---|
| **Files modified** | `backend/services/llm_services.py` (constructor accepts `retriever`, prompt template gets `RETRIEVED KNOWLEDGE:` block, `analyze()` calls retriever in try/except), `backend/routes/llm.py` (one-line change to pass retriever into `create_llm_service`), `backend/main.py` (3 lines in `lifespan` to load the retriever) |
| **Main changes** | The prompt template gets a new section; everything else is unchanged |
| **Dependencies** | None new |
| **Data flow** | Same as today, with one extra `retriever.retrieve(...)` call inside `LLMService.analyze()` |
| **Testing** | `tests/test_rag_integration.py` — (1) `LLMService.analyze` with a mock retriever produces identical output structure to the non-RAG path; (2) when the retriever raises, `analyze` still returns a valid `LLMAnalysisOutput`; (3) when the retriever returns empty, the prompt contains the "none available" fallback string |
| **Risk** | Latency regression — mitigated by retrieving in `asyncio.to_thread` (same wrapper the existing LLM call uses) so it runs concurrently with the LLM call's startup if needed (or sequentially — adds ~300 ms which is fine) |

### Phase E — Testing and Evaluation

| | |
|---|---|
| **Files created** | `tests/test_*.py` (per phase), `notebooks/rag_evaluation.ipynb` |
| **Test types** | (1) Unit tests as above; (2) integration test: full `/api/assessment/process` returns a response with the same schema, just with grounded text; (3) manual eval notebook: 5–10 hand-picked assessments, compare LLM output with vs. without RAG for "groundedness" |
| **Acceptance criteria** | (a) Response schema unchanged, (b) at least 3 of 5 evaluation cases show measurably more specific recommendations (e.g. cites a specific retrofit type instead of generic "strengthen structure"), (c) latency budget held, (d) no increase in error rate |
| **Risk** | LLM output is non-deterministic — accept that, judge on qualitative improvement |

### Phase F — Deployment Considerations

| | |
|---|---|
| **Cold start on Render/Railway/Fly** | Add a `scripts/build_kb.py` that runs `python -m services.retrieval.chunk_loader` to pre-build the Chroma index at deploy time, **or** check in the pre-built `backend/data/chroma/` directory (Chroma SQLite is portable across machines) |
| **Myanmar VPN considerations** | None — RAG runs entirely locally, no new external API calls |
| **Disk size for deployment** | +130 MB (embedding model) + ~5 MB (Chroma index for 50 chunks) |
| **Versioning the KB** | Add `version` field to chunk frontmatter; rebuild index when KB version changes (simple script check) |
| **Env var** | `RESILIENCEAI_RAG_ENABLED=true` (default `true`, can be set `false` to disable at runtime without code change — useful for demos when you want to show "without RAG" vs "with RAG") |

---

## 12. Testing Strategy

| Level | What | How | Pass criteria |
|---|---|---|---|
| **Unit: chunk loader** | MD frontmatter parsing, tag extraction, duplicate ID detection | pytest with fixtures | Every MD parses; no duplicate IDs; missing required fields fail loudly |
| **Unit: retriever** | Per-channel query → top-k returns | pytest with mock Chroma + mock BM25 | Top-1 result for "mud_mortar_stone building" is the mud mortar chunk |
| **Unit: query builder** | Building context → expected query string + filter | pytest with fixed inputs | Snapshot test against expected queries |
| **Integration** | Full `analyze()` with mock retriever | pytest | Output is valid `LLMAnalysisOutput`; prompt contains expected `RETRIEVED KNOWLEDGE:` text |
| **Integration: failure isolation** | Retriever raises exception | pytest | `analyze()` returns valid output, logs warning |
| **Manual eval** | 5–10 hand-picked scenarios | `notebooks/rag_evaluation.ipynb` | Subjective — judge groundedness of recommendations |
| **End-to-end** | Full assessment through `/api/assessment/process` | manual + scripted | Schema unchanged; latency budget held |

---

## 13. Risks and Limitations

| Risk | Severity | Mitigation |
|---|---|---|
| **KB quality determines RAG value** | High | Phase A is human-authored; the model cannot write this well. Budget 8–15 hours of authoring. Start with the 10–15 highest-impact chunks; the system works with any non-empty KB. |
| **LLM may ignore retrieved context** | Medium | Add explicit prompt instruction: "Use the above authoritative knowledge to ground your assessment." Existing prompt is already strict about output format — strictness transfers. |
| **Embedding model adds 80 MB to deploy artifact** | Low | Acceptable for a school competition. Pin the model version in code. |
| **Chroma version churn** | Low | Pin `chromadb>=0.5,<1.0` in requirements. |
| **First-run download fails offline** | Low | Fallback: `retriever = None` → identical to today. For demos, pre-warm the cache once on a connected machine. |
| **BM25 is in-memory and rebuilt every boot** | Negligible | 50–75 chunks = sub-second rebuild |
| **Myanmar-specific sources may be hard to find** | Medium | UN-Habitat, EERI case studies, and the Sagaing Fault academic literature are the realistic sources. Myanmar National Building Code may be paywalled or restricted. |
| **LLM might cite knowledge that wasn't retrieved** | Low | The prompt says "use retrieved knowledge" but does not strictly require it. Acceptable — the alternative (forcing strict citation) requires re-architecting the output contract. |
| **Concurrent assessments hammering Chroma** | Negligible | Chroma handles concurrent reads. At competition scale (1 demo) this is moot. |

### Known limitations to be honest about

- The RAG system improves the **groundedness** of recommendations, not the underlying **accuracy** of the assessment. If the ML model is wrong, RAG doesn't fix that.
- The KB will never be exhaustive. For the competition, the goal is "clearly grounded in real sources," not "covers every possible failure mode."
- The retrieval query is deterministic. A future improvement could be a learned re-ranker, but that's out of scope.

---

## 14. Clear Recommendation: What to Implement First

**Build in this order, in this priority, with these time estimates** (for one person, ~10–15 hrs total):

1. **Phase A — KB authoring, BUT START WITH ONLY 10–15 CHUNKS** (4–6 hrs)
   - Must-haves first: `local_context/sagaing_fault.md`, `local_context/yangon_soft_soil.md`, `building_vulnerability/materials_overview.md`, one chunk per main superstructure material, `mitigation/retrofitting_overview.md`, `environmental/soil_amplification.md`, `earthquake_safety/{before,during,after}.md`
   - The system works with any non-empty KB. Don't wait to have 75 chunks.

2. **Phase C — Retrieval service (the hardest part to get right)** (3–4 hrs)
   - Skip Phase B's "build index at startup" cleverness; just load chunks + embed + upsert on first import
   - Implement hybrid retrieval with RRF
   - Get one passing end-to-end retrieval test working

3. **Phase D — LLM integration** (1–2 hrs)
   - One-line prompt change
   - One constructor change
   - Fallback paths in place

4. **Phase E — Quick manual eval** (1–2 hrs)
   - Pick 3 assessments, run them, eyeball the recommendations
   - If groundedness improved → ship it
   - If not → debug, add more KB chunks, iterate

5. **Phases B/F — Index persistence, deployment** (1 hr)
   - Add `scripts/build_kb.py`
   - Decide whether to ship the Chroma directory with the repo or rebuild on first boot

**Skip for v1** (do not implement now):
- Citations in LLM output (breaks contract, defer to v2)
- BM25 reindexing endpoints
- A frontend "Sources" panel
- Re-ranking models
- Metadata-only "draft" workflow for KB authors

### The single most important thing

**The KB content quality is what will make or break this feature.** If the LLM has access to 10 well-written, well-sourced, specific chunks about Myanmar earthquake risk and mud mortar stone construction, the recommendations will visibly improve. If it has 75 generic chunks scraped from a generic earthquake safety website, the recommendations will be just as generic as they are today. **Spend the time on Phase A.**

---

## Appendix: Things I noticed during inspection (not RAG-related, but flagging)

These are pre-existing issues I noticed in the codebase while mapping the architecture. They are out of scope for the RAG task but worth addressing before the Aug 1 demo:

1. **Priority color inconsistency**: `project_schema.py:130` documents `LLMRecommendation.priority` as `"red" | "yellow" | "blue"`, but the prompt in `llm_services.py:197` uses `"red" | "orange" | "yellow" | "green"`. Reconcile before the demo.
2. **Stray debug print**: `main.py:21` has `print("Database reset complete")` at module top-level. Remove for the demo.
3. **`routes/llm.py` instantiates `llm_service` at module load time** (line 14). This means if the LLM service fails to initialize (e.g. missing API key), the entire `routes` import fails. Consider lazy initialization.

---

*End of plan. No project files were modified during planning. The plan above is the only artifact produced.*
