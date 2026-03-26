"""
Google Cloud Trace + Monitoring (replaces Azure Monitor).

BEFORE: configure_azure_monitor(connection_string=...)
AFTER:  OpenTelemetry → Cloud Trace exporter
"""
import os
import logging

logger = logging.getLogger("brand-guardian-telemetry")


def setup_telemetry():
    """Initialize Google Cloud Trace via OpenTelemetry."""
    project_id = os.getenv("GCP_PROJECT_ID")

    if not project_id:
        logger.warning("No GCP_PROJECT_ID found. Telemetry is DISABLED.")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        tracer_provider = TracerProvider()
        cloud_trace_exporter = CloudTraceSpanExporter(project_id=project_id)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(cloud_trace_exporter)
        )
        trace.set_tracer_provider(tracer_provider)

        logger.info("☁️ Google Cloud Trace enabled!")

    except ImportError:
        logger.warning("OpenTelemetry GCP packages not installed. Skipping.")
    except Exception as e:
        logger.error(f"Failed to initialize Cloud Trace: {e}")
