# Task: Plan a RAG System for the Earthquake Resilience AI Project

You are working on the local project folder for an earthquake building resilience AI system.

## SCOPE

You may:

* Read the entire local project folder.
* Read the specified project GitHub repository for additional context.
* Run read-only inspection commands.
* Research relevant technical options if necessary.

At this stage, you must **NOT modify any files**.

Do not:

* Create files.
* Edit files.
* Install dependencies.
* Modify the ML model.
* Modify the hazard engine.
* Modify the resilience calculation.
* Modify the frontend.
* Modify the existing LLM implementation.

Your task is to understand the project and produce a detailed implementation plan only.

---

# PROJECT CONTEXT

The project currently combines:

```text
Building features
        ↓
ML model
        ↓
Damage prediction / resilience assessment

Location
        ↓
Hazard engine
        ↓
Environmental hazard assessment

Assessment results
        ↓
LLM
        ↓
Risk interpretation
Key findings
Recommendations
```

The goal is to add **Retrieval-Augmented Generation (RAG)** to the existing LLM system.

The RAG system should provide relevant, authoritative earthquake and building-safety knowledge to the LLM so that its explanations and recommendations are better grounded.

---

# PHASE 1 — UNDERSTAND THE EXISTING PROJECT

Inspect the project thoroughly and trace the actual architecture.

Identify:

## Backend

* Framework
* Main application structure
* Relevant services
* Assessment routes
* Assessment pipeline
* LLM service
* Pydantic schemas or equivalent response models

## LLM pipeline

Determine:

1. Where the assessment is processed.
2. Where the final assessment context is created.
3. What data is passed to the LLM.
4. What prompts are currently used.
5. What model/API is used.
6. What structured output is required.
7. How LLM errors are handled.
8. How the LLM response reaches the frontend.

Create a clear flow such as:

```text
Assessment Request
        ↓
Building Model
        ↓
Hazard Engine
        ↓
Assessment Context
        ↓
LLM Prompt
        ↓
Structured LLM Response
        ↓
Frontend
```

Use the actual project architecture, not assumptions.

---

# PHASE 2 — DETERMINE THE BEST RAG ARCHITECTURE

Research and compare practical options for this project.

The architecture should prioritize:

* Reliability
* Low cost
* Low complexity
* Fast retrieval
* Easy local development
* Easy deployment
* Suitability for a school AI competition

Evaluate:

## Knowledge storage

Possible approaches:

* Markdown/text files
* JSON documents
* SQLite
* Chroma
* FAISS
* Other lightweight vector databases

## Embeddings

Consider:

* Local embedding models
* API-based embeddings
* Existing project dependencies
* Cost
* Deployment complexity

## Retrieval

Determine:

* How assessment data should be converted into a retrieval query.
* Whether to use semantic search, keyword search, or hybrid search.
* How many chunks should be retrieved.
* How relevance should be evaluated.
* How to prevent irrelevant information from being passed to the LLM.

Do not select a technology merely because it is popular. Recommend the option that best fits this specific project.

---

# PHASE 3 — DESIGN THE KNOWLEDGE BASE

Determine what information should be included.

Potential categories:

## Earthquake safety

* Before an earthquake
* During an earthquake
* After an earthquake

## Building vulnerability

* Structural systems
* Building materials
* Building age
* Number of floors
* Foundation conditions
* Soft stories
* Structural irregularity
* Weak connections

## Mitigation

* Retrofitting
* Structural strengthening
* Maintenance
* Securing heavy objects
* Foundation and soil considerations

## Environmental hazards

* Soil amplification
* Fault proximity
* Historical seismicity

## Local context

Investigate whether authoritative Myanmar-specific earthquake or building-safety sources would be useful.

Prioritize:

* Government sources
* Universities
* Recognized earthquake engineering organizations
* International disaster-risk organizations
* Official codes and engineering guidance

For each source category, explain:

* Why it is useful.
* Whether it should be included.
* How reliable it is.
* What metadata should be retained.

---

# PHASE 4 — DESIGN THE RETRIEVAL FLOW

Design how a real assessment should retrieve information.

For example:

```text
Assessment:
- Older building
- Multiple floors
- High soil hazard
- Low resilience
        ↓
Construct retrieval query
        ↓
Retrieve relevant knowledge
        ↓
Pass assessment + knowledge to LLM
        ↓
Generate grounded response
```

Determine:

* What fields should be included in the retrieval query.
* How to avoid overloading the query with irrelevant information.
* Whether retrieval should differ for:

  * Building vulnerability
  * Soil hazard
  * Fault proximity
  * Historical seismicity
  * Recommendations

Recommend an appropriate retrieval strategy.

---

# PHASE 5 — DESIGN LLM INTEGRATION

Determine the minimum changes required to the existing LLM system.

The existing response contract must be preserved.

The plan should explain:

```text
Assessment context
        +
Retrieved knowledge
        ↓
Existing LLM prompt
        ↓
Existing structured output
```

Determine:

* Where retrieval should occur.
* How retrieved context should be inserted into the prompt.
* How sources should be represented.
* Whether citations should be included in the LLM output.
* How the system should behave if no relevant documents are found.

Do not redesign the entire LLM system unnecessarily.

---

# PHASE 6 — FAILURE AND FALLBACK DESIGN

Design failure behavior for:

* Vector database failure
* Embedding failure
* No relevant results
* LLM API failure
* Excessively large retrieved context
* Missing knowledge-base data

The RAG system should not unnecessarily break the entire assessment pipeline.

Recommend graceful fallback behavior.

---

# PHASE 7 — IMPLEMENTATION PLAN

Produce a phased implementation plan.

For each phase, specify:

1. Files likely to be created or modified.
2. Main functions/classes required.
3. Dependencies required.
4. Data flow.
5. Testing requirements.
6. Risks.

The plan should distinguish between:

### Phase A — Knowledge base creation

### Phase B — Embedding/index generation

### Phase C — Retrieval service

### Phase D — LLM integration

### Phase E — Testing and evaluation

### Phase F — Deployment considerations

---

# FINAL OUTPUT

Do not modify the project.

Return a detailed but practical plan containing:

1. Summary of the existing project architecture.
2. Current LLM data flow.
3. Recommended RAG architecture.
4. Recommended technology choices and alternatives.
5. Knowledge-base design.
6. Retrieval strategy.
7. LLM integration plan.
8. Failure/fallback strategy.
9. Proposed file structure.
10. Dependency changes required.
11. Step-by-step implementation plan.
12. Testing strategy.
13. Risks and limitations.
14. Clear recommendation of what should be implemented first.

The plan should be specific to the actual project after inspecting the codebase, not a generic RAG tutorial.

Do not edit any files during this task.
