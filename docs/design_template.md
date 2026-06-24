# Design Template

## Problem

Build a research assistant that can answer complex questions by searching the web, analyzing information, and writing a structured answer. The system must handle queries that require multi-step reasoning, source evaluation, and synthesis.

## Why multi-agent?

Single-agent struggles with:
- Maintaining focus across search, analysis, and writing in one prompt
- Providing structured intermediate artifacts (research notes, analysis) for debugging
- Scaling to complex queries where different skills (search, critique, writing) need specialized prompts
- Clear separation of concerns for tracing and cost attribution

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Route query to next worker or stop | Full state + iteration count | Route decision (researcher/analyst/writer/done) | Max iterations exceeded |
| Researcher | Search for sources + write research notes | User query | `research_notes`, `sources` | Search API failure, empty results |
| Analyst | Extract claims, compare viewpoints, flag gaps | `research_notes` | `analysis_notes` | Weak or missing research notes |
| Writer | Synthesize final answer with citations | `research_notes` + `analysis_notes` + `sources` | `final_answer` | Missing research context |
| Critic (optional) | Fact-check + safety review | `final_answer` + `sources` | Verdict + feedback | No final answer to review |

## Shared state

Fields in `ResearchState` and why:
- `request`: original query (immutable reference)
- `iteration`: guard against infinite loops
- `route_history`: audit trail of agent calls
- `sources`: documents found by researcher (for citation)
- `research_notes`: raw research output (handoff to analyst)
- `analysis_notes`: structured insights (handoff to writer)
- `final_answer`: final output (deliverable)
- `agent_results`: per-agent cost + token tracking
- `trace`: structured event log for debugging
- `errors`: failure records for fallback logic

## Routing policy

1. Supervisor checks `state.iteration >= max_iterations` → done
2. If no `research_notes` → route to researcher
3. If no `analysis_notes` → route to analyst
4. If no `final_answer` → route to writer
5. Else → done (optionally route to critic for review)

Graph flow: supervisor → researcher → supervisor → analyst → supervisor → writer → supervisor → (critic) → supervisor → done

## Guardrails

- Max iterations: 6 (configurable via MAX_ITERATIONS env var)
- Timeout: 60s per LLM call (configurable via TIMEOUT_SECONDS)
- Retry: exponential backoff (3 attempts) for RateLimitError, APITimeoutError, APIError
- Fallback: if Tavily is unavailable, fall back to mock search results
- Validation: Pydantic schema validation on all state transitions

## Benchmark plan

| Query | Metric | Expected outcome |
|---|---|---|
| "What is GraphRAG?" | latency, cost, quality | Multi-agent produces more structured answer with citations |
| "Compare RAG vs fine-tuning" | latency, cost, quality | Multi-agent handles comparison better via analyst role |
| "Explain multi-agent systems" | citation coverage | Multi-agent cites more sources |
