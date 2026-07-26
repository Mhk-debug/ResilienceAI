# Future Improvements

> **Known limitations, planned improvements, and technical debt for the ResilienceAI backend**

---

## Known Limitations

### 1. ML Model Limitations

| Limitation | Severity | Description |
|------------|----------|-------------|
| **Nepal-specific training** | High | Model trained on 2015 Gorkha earthquake (Nepal) building stock. May not generalize to Myanmar typologies (bamboo, traditional timber, different codes). |
| **No uncertainty quantification** | Medium | Point predictions only. No confidence intervals or prediction distributions. |
| **Ordinal target as classification** | Low | XGBoost trained as multi-class (not ordinal). Trees handle this empirically but not optimal. |
| **Single event training** | Medium | Only one earthquake event in training data. No magnitude/distance conditioning. |
| **Material flag assumptions** | Medium | Exactly one material flag expected, but real buildings mix materials. |

### 2. Hazard Engine Limitations

| Limitation | Severity | Description |
|------------|----------|-------------|
| **Hardcoded fault database** | High | Only 10 major faults. Misses local/unknown faults. No dynamic fault database. |
| **SoilGrids resolution** | Medium | 250m resolution, top 30cm only. No site-specific investigation data. |
| **Liquefaction model simplified** | Medium | LSI heuristic only. No groundwater depth, no SPT/CPT, no cyclic stress ratio. |
| **GMPE approximations** | Medium | Empirical MMI/PGA from events, not region-calibrated GMPEs. |
| **USGS catalog completeness** | Low | M4.5+ only, instrumental period only. Misses historical/pre-instrumental events. |
| **Stationary recurrence** | Low | Gutenberg-Richter assumes Poisson process. No time-dependent models. |
| **Additive score combination** | Low | Components added in raw space. No interaction modeling. |

### 3. RAG System Limitations

| Limitation | Severity | Description |
|------------|----------|-------------|
| **Small knowledge base** | High | ~42 chunks across 15 documents. Limited coverage of earthquake engineering topics. |
| **No re-ranking** | Medium | Only cosine similarity + tag boost. No cross-encoder re-ranker. |
| **Static index** | Medium | No incremental updates. Full rebuild required for new documents. |
| **Single embedding model** | Medium | `all-MiniLM-L6-v2` only. No ensemble or domain adaptation. |
| **Heuristic tag boosting** | Low | +0.05 per tag is arbitrary, not learned. |
| **No query expansion** | Low | Direct query use only. No synonyms/related terms. |

### 4. LLM Integration Limitations

| Limitation | Severity | Description |
|------------|----------|-------------|
| **Single provider (Gemini)** | High | No fallback if Gemini unavailable. Region-dependent (Myanmar VPN issues). |
| **No streaming output** | Medium | Full response waited. SSE pipeline already exists but not for LLM. |
| **Fixed temperature (0.1)** | Low | Less creative, may miss nuanced recommendations. |
| **Post-hoc evidence validation** | Medium | Hallucinated citations filtered after generation, not prevented. |
| **String concatenation prompts** | Low | Not templated. Harder to maintain/version. |
| **No few-shot examples** | Low | Zero-shot only. Could improve consistency with examples. |

### 5. Infrastructure & Operations

| Limitation | Severity | Description |
|------------|----------|-------------|
| **Single-threaded ML inference** | Medium | XGBoost blocks event loop. Uses `asyncio.to_thread()` but no worker pool. |
| **No ChromaDB connection pooling** | Low | New client per retriever instantiation. |
| **No structured logging** | Medium | No correlation IDs, no JSON logs, no distributed tracing. |
| **Sync geocoding in async route** | Medium | `geopy.Nominatim` blocks event loop in `assessment.py`. |
| **No request validation middleware** | Low | Relies only on Pydantic. No rate limiting, no auth. |
| **CORS hardcoded** | Low | Production domains need manual update. |

---

## Planned Improvements (Priority Order)

### P0 - Critical (Blocking Production/Scale)

1. **ML Model Retraining for Myanmar**
   - Collect/generate Myanmar building damage data
   - Retrain XGBoost with local typologies
   - Add magnitude/distance as features

2. **Gemini Fallback Provider**
   - Add Anthropic Claude / OpenAI as fallback
   - Implement provider abstraction in `GenAIClient`
   - Automatic failover on rate limits/errors

3. **Dynamic Fault Database**
   - Integrate USGS Quaternary Faults / GEM Global Fault Database
   - Replace hardcoded polylines with queryable fault service

4. **Structured Logging & Observability**
   - Add `structlog` with JSON output
   - Correlation IDs across SSE stages
   - OpenTelemetry integration for distributed tracing

### P1 - High (Significant Value)

5. **RAG Enhancements**
   - Add cross-encoder re-ranker (e.g., `bge-reranker-base`)
   - Expand knowledge base to 200+ chunks
   - Implement incremental index updates
   - Add query expansion with domain synonyms

6. **Hazard Engine Improvements**
   - Integrate region-calibrated GMPEs (e.g., `OpenQuake` GMPEs)
   - Add VS30 proxy from topography for soil amplification
   - Implement logic tree for epistemic uncertainty

7. **LLM Streaming & Prompt Templating**
   - Add streaming Gemini response to SSE pipeline
   - Move prompts to Jinja2 templates
   - Add few-shot examples for consistent output

8. **Async Hazard Engine**
   - Parallelize USGS + SoilGrids + Fault queries
   - Add result caching (Redis) with 24h TTL
   - Background pre-computation for common locations

### P2 - Medium (Quality of Life)

9. **ML Uncertainty Quantification**
   - Add conformal prediction intervals
   - Or quantile regression XGBoost
   - Expose confidence in resilience score

10. **Database & API Hardening**
    - Add request rate limiting
    - API key authentication
    - Pagination for assessment history
    - Soft delete for assessments

11. **Testing & CI/CD**
    - Increase test coverage to >80%
    - Add integration tests for full pipeline
    - GitHub Actions for test + build
    - Automated dependency updates

12. **Documentation & Developer Experience**
    - Auto-generate API docs from Pydantic models
    - Add architecture decision records (ADRs)
    - Interactive notebook for model exploration

### P3 - Low (Nice to Have)

13. **Multi-Hazard Support**
    - Add flood hazard (Myanmar monsoon)
    - Add cyclone/wind hazard
    - Unified multi-hazard risk score

14. **Advanced Frontend Features**
    - Building portfolio assessment (batch)
    - Retrofit cost estimator
    - Comparative scenario analysis

15. **Model Explainability**
    - SHAP values for ML predictions
    - Feature importance in LLM context
    - Counterfactual explanations ("what if foundation changed?")

---

## Technical Debt

| Area | Debt Item | Effort | Risk |
|------|-----------|--------|------|
| `main.py` | Lifespan does too much; split into init functions | Low | Medium |
| `project_schema.py` | Monolithic; split into domain modules | Medium | Low |
| `hazard_engine/` | 12 separate files for one pipeline; consider consolidation | Medium | Low |
| `retrieval/` | Query builder tightly coupled to schema fields | Medium | Medium |
| `llm_services.py` | `LLMService` does too much (retrieve + prompt + generate + validate) | Medium | Medium |
| `assessment.py` | 360-line function; extract stage handlers | High | Medium |
| `pipeline.py` | `StructuralFeatureExtractor` not picklable (sklearn issue) | Low | Low |
| Tests | No fixtures for common test data; duplication | Medium | Low |
| Config | Constants scattered across modules; centralize | Low | Low |

---

## Architecture Decision Records (ADRs) Needed

| Topic | Status |
|-------|--------|
| Why XGBoost over LightGBM/CatBoost? | Documented in ML doc |
| Why deterministic hazard over ML? | Documented in hazard doc |
| Why ChromaDB over Pinecone/Weaviate? | Needs ADR |
| Why Gemini over other LLMs? | Needs ADR |
| Why JSONB over relational columns? | Needs ADR |
| Why SSE over WebSocket? | Needs ADR |
| Why `asyncio.to_thread` for ML vs worker pool? | Needs ADR |

---

## Dependency Updates Needed

| Package | Current | Target | Notes |
|---------|---------|--------|-------|
| `fastapi` | 0.115.0 | 0.115+ | Check breaking changes |
| `pydantic` | 2.9.2 | 2.10+ | v2.10 has performance improvements |
| `xgboost` | 2.1.3 | 3.0+ | Major version - test carefully |
| `google-genai` | 1.5.0 | Latest | Rapid API changes |
| `chromadb` | 0.5.5 | 1.0+ | Major version - breaking changes likely |
| `sentence-transformers` | 3.1.1 | 3.2+ | New models available |

---

## Migration Paths

### ML Model v2 (Myanmar-trained)
1. Collect/generate training data
2. Retrain with same feature engineering pipeline
3. Validate against Nepal test set + Myanmar holdout
4. A/B test in production with feature flag
5. Full rollout after validation

### Hazard Engine v2 (GMPE-based)
1. Add `openquake` as dependency
2. Implement GMPE selector by region
3. Compare deterministic vs GMPE scores
4. Run parallel in shadow mode
5. Switch after calibration

### RAG v2 (Re-ranker + Larger KB)
1. Expand knowledge base (target 200 chunks)
2. Add cross-encoder re-ranker
3. Evaluate retrieval metrics (recall@5, MRR)
4. A/B test LLM output quality
5. Deploy

---

## Resource Estimates

| Improvement | Dev Time | Infra Cost | Dependencies |
|-------------|----------|------------|--------------|
| Myanmar ML retraining | 2-4 weeks | Low (CPU) | Labeled data |
| Gemini fallback | 1 week | API costs | Anthropic/OpenAI accounts |
| Dynamic faults | 1-2 weeks | Low | USGS/GEM data access |
| Structured logging | 3-5 days | Low | OpenTelemetry collector |
| RAG re-ranker | 1 week | GPU (inference) | `sentence-transformers` cross-encoder |
| GMPE integration | 2-3 weeks | Medium | `openquake` license |
| LLM streaming | 3-5 days | Low | Gemini streaming API |
| Test coverage | 2-3 weeks | CI minutes | - |

---

## Decision Framework for New Features

Before adding features, evaluate:

1. **User Impact**: Does this directly improve assessment quality or UX?
2. **Maintenance Burden**: Will this require ongoing updates (data, models, APIs)?
3. **Failure Modes**: What happens when this component fails? Graceful degradation?
4. **Testing**: Can we validate this automatically?
5. **Documentation**: Is the design documented for future maintainers?

**Default to "No"** unless clear positive answers to above.

---

## Contact & Ownership

| Component | Owner | Last Updated |
|-----------|-------|--------------|
| ML Pipeline | - | 2026-07-26 |
| Hazard Engine | - | 2026-07-26 |
| RAG System | - | 2026-07-26 |
| LLM Integration | - | 2026-07-26 |
| Database/API | - | 2026-07-26 |
| Documentation | - | 2026-07-26 |

*Update ownership when team grows.*