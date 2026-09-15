# Project Latency Documentation

This document reflects the latency actually visible in the terminal logs you pasted, not a generic estimate.

## What the logs show

From the runtime logs, the request path was:

1. Guardrail check
2. Planner decision
3. Retrieval + reranking
4. Final Portkey LLM response generation

The key observed timings are:

```text
09:45:44.017 Guardrails Check with LLM
09:45:48.460 Guardrails passed.
09:45:48.460 Planner Decision
09:45:53.856 Intent is identified as CONVERSATIONAL
09:45:53.863 LLM Synthesis
09:46:05.262 Response synthesised via LLM.
```

This request completed in roughly 21 seconds from guardrail start to final answer.

Another technical request shows a similar pattern:

```text
09:47:15.871 Guardrails Check with LLM
09:47:20.002 Guardrails passed.
09:47:20.014 Planner Decision
09:47:30.962 Intent is identified as ...
09:47:30.975 Retrieving Knowledge
09:47:32.486 Retrieved results from Qdrant
09:47:32.491 FlashRank reranking started
09:47:33.132 Reranking complete
09:47:33.133 Generating Technical Response
09:47:48.175 Response synthesised via LLM.
```

This second request took roughly 32 seconds end-to-end.

## Per-stage breakdown from the terminal logs

| Stage | Observed timing | Notes |
| --- | ---: | --- |
| Guardrail evaluation | ~4.4s | Gemini/Nemo check before the request proceeds |
| Planner decision | ~5.4s | LLM-based routing decision |
| Retrieval + reranking | ~2.6s | Qdrant + FlashRank |
| Final response generation | ~15s | Final Portkey LLM call |
| Total request latency | ~21s to ~32s | Based on the logged samples |

## Main bottlenecks

### 1. Sequential LLM calls
The logs clearly show multiple remote model calls in sequence:

- guardrail evaluation
- planner
- final synthesis

This is the biggest contributor to latency.

### 2. Retrieval and reranking
The technical query path included:

- Qdrant embedding lookup
- semantic reranking with FlashRank
- context trimming before answer generation

This adds a measurable delay, but it is still smaller than the total LLM time in your logs.

### 3. External service dependency
The app depends on:

- Gemini
- Portkey
- Qdrant
- Logfire

Because these are external services, response time depends on provider latency and network conditions.

## Important note about the auto-reload warnings

The uvicorn output also contains messages like:

```text
WatchFiles detected changes ... Reloading...
```

These cause app restarts, but they are not the primary reason for the request delays in your logs. The main latency is the model + retrieval workflow itself.

## Practical conclusion

From the actual terminal evidence, this project is not “fast” in the low hundreds of milliseconds range. It is operating in the tens-of-seconds range for real requests because it is doing multiple external model calls and retrieval operations.

## Recommended fixes

1. Reduce LLM round trips
   - avoid separate planner + final answer calls when possible
   - combine tasks or simplify routing logic

2. Cache repeated responses
   - use Portkey response caching more aggressively

3. Keep retrieval smaller and tighter
   - reduce top-k chunk count
   - use concise context windows
   - limit reranking workload

4. Make guardrails cheaper
   - run deterministic phrase checks before expensive LLM guardrail generation

5. Add latency logging per stage
   - track planner time, retrieval time, and answer generation time separately

## Summary

Based on the logs you shared, the latency is dominated by external service calls, especially the sequential LLM calls. The project is currently running in the roughly 20–32 second request range for the logged requests, which is consistent with the architecture shown in the terminal output.
