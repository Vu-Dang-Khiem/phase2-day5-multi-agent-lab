# Benchmark Report

Generated: 2026-06-24 12:18:00

## Summary

| Run | Latency (s) | Cost (USD) | Quality (0-10) | Notes |
|---|---:|---:|---:|:---|
| baseline-research-agent-bench | 7.57 | 0.000000 | 8.0 | citation_coverage=0% |
| multi-agent-research-agent-bench | 7.83 | 0.000000 | 8.0 | citation_coverage=100% |
| baseline-multi-agent-briefing | 11.76 | 0.000000 | 9.0 | citation_coverage=0% |
| multi-agent-multi-agent-briefing | 8.18 | 0.000000 | 8.0 | citation_coverage=0% |
| baseline-experiment-design | 7.68 | 0.000000 | 9.0 | citation_coverage=0% |
| multi-agent-experiment-design | 15.14 | 0.000000 | 8.0 | citation_coverage=100% |
| baseline-survey-blueprint | 20.90 | 0.000000 | 9.0 | citation_coverage=0% |
| multi-agent-survey-blueprint | 15.69 | 0.000000 | 8.0 | citation_coverage=0% |

## Comparison

- **research-agent-bench**: multi-agent latency +3% vs baseline, quality 8.0/10 (+0.0 vs baseline)
- **multi-agent-briefing**: multi-agent latency -30% vs baseline, quality 8.0/10 (-1.0 vs baseline)
- **experiment-design**: multi-agent latency +97% vs baseline, quality 8.0/10 (-1.0 vs baseline)
- **survey-blueprint**: multi-agent latency -25% vs baseline, quality 8.0/10 (-1.0 vs baseline)

## Key Findings

- **Latency**: Multi-agent is generally slower (+3% to +97%), but can be faster (-30%, -25%) when baseline triggers retries or generates longer outputs
- **Quality**: Baseline scored equal or better on 3/4 prompts; multi-agent never surpassed baseline quality
- **Citation Coverage**: Multi-agent achieved 100% citation coverage on 2/4 prompts vs 0% for baseline on all prompts
- **Cost**: Both at $0 (Groq free tier); with paid models, multi-agent would cost ~3-4x more due to multiple LLM calls per query

## Methodology

- Latency: wall-clock time from query start to final answer.
- Cost: estimated from token usage using provider pricing.
- Quality: LLM-as-judge score (0-10) based on accuracy, completeness, clarity, citations.
- Notes include citation coverage (fraction of sources cited in final answer).
