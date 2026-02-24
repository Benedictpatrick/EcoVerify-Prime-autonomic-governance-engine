"""OpenTelemetry tracing initialisation and agent-span decorator.

Provides:
  - ``init_telemetry()``  — call once at startup to configure the tracer provider.
  - ``@agent_span(name)`` — decorator to wrap agent node functions in OTel spans.
  - ``get_tracer()``      — returns the shared tracer for manual span creation.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from ecoverify.config import settings

logger = logging.getLogger(__name__)


_initialised = False


def init_telemetry(service_name: str = "ecoverify-prime") -> None:
    """Set up the OpenTelemetry TracerProvider.

    Uses ``ConsoleSpanExporter`` in dev.  If ``OTEL_EXPORTER_OTLP_ENDPOINT``
    is set, adds an OTLP/gRPC exporter for production observability.
    """
    global _initialised
    if _initialised:
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # Always add console exporter for local visibility
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Optional OTLP exporter
    endpoint = settings.otel_exporter_otlp_endpoint
    if endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            otlp = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(otlp))
            logger.info("OTLP exporter configured → %s", endpoint)
        except ImportError:
            logger.warning("opentelemetry-exporter-otlp not installed; skipping OTLP export.")

    trace.set_tracer_provider(provider)
    _initialised = True
    logger.info("OpenTelemetry initialised for service '%s'.", service_name)


def get_tracer(name: str = "ecoverify.agents") -> trace.Tracer:
    """Return a tracer instance."""
    return trace.get_tracer(name)


def agent_span(span_name: str) -> Callable:
    """Decorator that wraps an agent node function in an OpenTelemetry span.

    Records ``agent.name``, input state key count, execution duration, and
    sets the span status to ERROR with exception details on failure.

    Usage::

        @agent_span("vanguard_node")
        def vanguard_node(state: EcoVerifyState) -> dict:
            ...
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(state: dict, *args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            with tracer.start_as_current_span(
                span_name,
                attributes={
                    "agent.name": span_name,
                    "agent.input_keys": str(list(state.keys())[:20]),
                },
            ) as span:
                t0 = time.perf_counter()
                try:
                    result = fn(state, *args, **kwargs)
                    span.set_attribute("agent.duration_ms", round((time.perf_counter() - t0) * 1000, 2))
                    span.set_status(trace.StatusCode.OK)
                    return result
                except Exception as exc:
                    span.set_status(trace.StatusCode.ERROR, str(exc))
                    span.record_exception(exc)
                    raise

        @functools.wraps(fn)
        async def async_wrapper(state: dict, *args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            with tracer.start_as_current_span(
                span_name,
                attributes={
                    "agent.name": span_name,
                    "agent.input_keys": str(list(state.keys())[:20]),
                },
            ) as span:
                t0 = time.perf_counter()
                try:
                    result = await fn(state, *args, **kwargs)
                    span.set_attribute("agent.duration_ms", round((time.perf_counter() - t0) * 1000, 2))
                    span.set_status(trace.StatusCode.OK)
                    return result
                except Exception as exc:
                    span.set_status(trace.StatusCode.ERROR, str(exc))
                    span.record_exception(exc)
                    raise

        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(fn) else wrapper

    return decorator
