"""OpenTelemetry-compatible trace correlation for the concierge.

Uses Azure Monitor OpenTelemetry when App Insights is configured; falls back to
a no-op tracer so the agent still runs locally without telemetry.
"""
from __future__ import annotations
import logging, os
from contextlib import contextmanager
from typing import Iterator, Any

log = logging.getLogger("contoso.telemetry")

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    _tracer = trace.get_tracer("contoso.travel.concierge")
    _HAVE_OTEL = True
except Exception:
    _tracer = None
    _HAVE_OTEL = False

_APP_INSIGHTS_ENABLED = False

def init_telemetry() -> None:
    """Wire Azure Monitor OpenTelemetry if a connection string is present."""
    global _APP_INSIGHTS_ENABLED
    conn = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    if not conn:
        log.info("App Insights not configured; running without telemetry export.")
        return
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        configure_azure_monitor(connection_string=conn, logger_name="contoso")
        _APP_INSIGHTS_ENABLED = True
        log.info("App Insights telemetry enabled.")
    except Exception as e:
        log.warning("Failed to enable App Insights telemetry: %s", e)

@contextmanager
def span(name: str, **attrs: Any) -> Iterator[Any]:
    """Start a span. Attaches attributes as span attributes when OTel is present."""
    if not _HAVE_OTEL or _tracer is None:
        yield None
        return
    with _tracer.start_as_current_span(name) as sp:
        for k, v in attrs.items():
            try:
                sp.set_attribute(f"contoso.{k}", v)
            except Exception:
                pass
        try:
            yield sp
        except Exception as e:
            sp.set_status(Status(StatusCode.ERROR, str(e)))
            raise

def set_span_attr(key: str, value: Any) -> None:
    if not _HAVE_OTEL:
        return
    sp = trace.get_current_span()
    try:
        sp.set_attribute(f"contoso.{key}", value)
    except Exception:
        pass
