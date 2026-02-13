from core import settings
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased


def setup_tracing(service_name: str = "auth_service"):
    # Самплинг
    sampler = ParentBased(TraceIdRatioBased(settings.otel_sampling_ratio))

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name or service_name,
            "service.version": settings.otel_service_version,
            "deployment.environment": settings.otel_environment,
        }
    )

    provider = TracerProvider(resource=resource, sampler=sampler)
    trace.set_tracer_provider(provider)

    exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        timeout=5,
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))


def instrument_app(app):
    def server_request_hook(span, scope):
        if not span:
            return
        headers = dict(scope.get("headers") or [])
        for k, v in headers.items():
            if k.decode().lower() == "x-request-id":
                span.set_attribute("request.id", v.decode())
                break

    FastAPIInstrumentor.instrument_app(
        app, server_request_hook=server_request_hook, excluded_urls="(/health|/ping)"
    )
    RedisInstrumentor().instrument()
