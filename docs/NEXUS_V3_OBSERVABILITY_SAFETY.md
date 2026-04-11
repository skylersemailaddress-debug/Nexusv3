# Nexus V3 Observability and Enterprise Safety

## Added in this step
- Request logging middleware with request IDs
- CORS allowlist for local UI origin
- Audit logging for write actions
- Readiness and liveness health endpoints
- Admin-only support bundle route
- Support bundle export script

## Current files
- runtime/control/services/observability_service.py
- runtime/control/routes/ops.py
- runtime/ops/export-support-bundle.ps1

## Next hardening moves
- rate limiting
- secure headers middleware
- dependency and secret scanning
- stronger input validation models
- external error tracking
