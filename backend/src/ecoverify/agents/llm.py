"""Shared LLM factory for EcoVerify-Prime agent nodes.

Provides a singleton ChatOpenAI instance gated by the ``ECOVERIFY_LLM_ENABLED``
feature flag.  When the flag is ``False`` (or no API key is set), callers fall
back to deterministic logic.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from ecoverify.config import settings

logger = logging.getLogger(__name__)


def is_llm_enabled() -> bool:
    """Check whether LLM integration is enabled **and** an API key is configured."""
    return bool(settings.llm_enabled and settings.openai_api_key)


@lru_cache(maxsize=1)
def get_chat_model():
    """Return a ``ChatOpenAI`` instance (cached singleton).

    Returns ``None`` when LLM is disabled — callers must check explicitly.
    """
    if not is_llm_enabled():
        logger.info("LLM disabled (llm_enabled=%s, api_key=%s)", settings.llm_enabled, bool(settings.openai_api_key))
        return None

    from langchain_openai import ChatOpenAI  # deferred import to avoid issues when LLM is off

    model = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.2,
        api_key=settings.openai_api_key,
        max_tokens=2048,
    )
    logger.info("ChatOpenAI initialised — model=%s", settings.openai_model)
    return model
