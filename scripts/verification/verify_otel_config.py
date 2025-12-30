
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from api.core.config import settings

print("--- Verifying OpenTelemetry Configuration ---")
print(f"OTEL_EXPORTER_OTLP_ENDPOINT: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")
print(f"OTEL_SERVICE_NAME: {settings.OTEL_SERVICE_NAME}")
print(f"OTEL_TRACE_SAMPLING_RATIO: {settings.OTEL_TRACE_SAMPLING_RATIO}")

# Verify types
if not isinstance(settings.OTEL_TRACE_SAMPLING_RATIO, float):
    print("Error: OTEL_TRACE_SAMPLING_RATIO should be a float.")
else:
    print("Type check passed.")
