from __future__ import annotations

import atexit
import logging
import os
from typing import Any
from urllib.parse import unquote

from opentelemetry import _logs, metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_shutdown_complete = False


def _resource() -> Resource:
    resource_attributes = {
        "service.name": os.getenv("OTEL_SERVICE_NAME", "checkout-service"),
        "service.namespace": os.getenv("SERVICE_NAMESPACE", "northstar-mercantile"),
        "service.version": os.getenv("SERVICE_VERSION", "0.1.0"),
        "deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT", "demo"),
    }
    return Resource.create(resource_attributes)


def _build_exporter_kwargs(signal_path: str) -> dict[str, Any] | None:
    base_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
    timeout_ms = int(os.getenv("OTEL_EXPORTER_OTLP_TIMEOUT", "10000"))
    if not base_endpoint or not headers:
        return None

    endpoint = f"{base_endpoint.rstrip('/')}/{signal_path.lstrip('/')}"
    parsed_headers = {}
    for pair in headers.split(","):
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        parsed_headers[key.strip()] = unquote(value.strip())
    return {
        "endpoint": endpoint,
        "headers": parsed_headers,
        "timeout": timeout_ms / 1000,
    }


def configure_telemetry() -> None:
    resource = _resource()

    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    metric_readers = []
    metric_exporter_kwargs = _build_exporter_kwargs("v1/metrics")
    if metric_exporter_kwargs:
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(**metric_exporter_kwargs),
            export_interval_millis=int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "15000")),
        )
        metric_readers.append(metric_reader)
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=metric_readers))

    logger_provider = LoggerProvider(resource=resource)
    _logs.set_logger_provider(logger_provider)

    span_exporter_kwargs = _build_exporter_kwargs("v1/traces")
    if span_exporter_kwargs:
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(**span_exporter_kwargs)))

    log_exporter_kwargs = _build_exporter_kwargs("v1/logs")
    if log_exporter_kwargs:
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(**log_exporter_kwargs)))

    LoggingInstrumentor().instrument(set_logging_format=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    root_logger.handlers.clear()
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] "
            "[trace_id=%(otelTraceID)s span_id=%(otelSpanID)s service=%(otelServiceName)s] "
            "%(message)s"
        )
    )
    root_logger.addHandler(stream_handler)

    if log_exporter_kwargs:
        root_logger.addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))

    def shutdown_telemetry() -> None:
        global _shutdown_complete
        if _shutdown_complete:
            return
        _shutdown_complete = True
        tracer_provider.shutdown()
        logger_provider.shutdown()

    atexit.register(shutdown_telemetry)
