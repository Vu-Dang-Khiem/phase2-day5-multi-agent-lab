"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

import logging
from dataclasses import dataclass
from time import perf_counter

from openai import APIError, APITimeoutError, OpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


GROQ_BASE_URL = "https://api.groq.com/openai/v1"

MODEL_COST_PER_1K_INPUT = {"gpt-4o-mini": 0.00015, "gpt-4o": 0.0025, "llama-3.3-70b-versatile": 0.0}
MODEL_COST_PER_1K_OUTPUT = {"gpt-4o-mini": 0.0006, "gpt-4o": 0.01, "llama-3.3-70b-versatile": 0.0}


class LLMClient:
    """Provider-agnostic LLM client with retry, timeout, and token tracking."""

    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.openai_model
        if settings.llm_provider == "groq":
            self._client = OpenAI(
                api_key=settings.groq_api_key,
                base_url=GROQ_BASE_URL,
                timeout=settings.timeout_seconds,
            )
            self._model = settings.groq_model
        else:
            self._client = OpenAI(
                api_key=settings.openai_api_key,
                timeout=settings.timeout_seconds,
            )
            self._model = settings.openai_model

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
    )
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        started = perf_counter()
        span_attrs = {"model": self._model}
        with trace_span("llm.complete", span_attrs):
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
        elapsed = perf_counter() - started
        choice = response.choices[0]
        content = choice.message.content or ""
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None
        cost = self._estimate_cost(input_tokens or 0, output_tokens or 0)

        logger.info(
            "LLM call model=%s input_tokens=%s output_tokens=%s cost=%.6f elapsed=%.2fs",
            self._model,
            input_tokens,
            output_tokens,
            cost,
            elapsed,
        )
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_rate = MODEL_COST_PER_1K_INPUT.get(self._model, 0.0005)
        output_rate = MODEL_COST_PER_1K_OUTPUT.get(self._model, 0.0015)
        return (input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)
