# Nexus V3 Production Readiness Checklist

## Runtime
- [x] restartable
- [x] validated
- [x] rollback path exists

## Data
- [x] durable local store
- [x] migration surface exists
- [ ] managed production database configured

## Security
- [x] auth and RBAC
- [x] typed write validation
- [x] secure headers
- [x] rate limiting
- [ ] dependency scanning automation
- [ ] secret scanning automation

## Observability
- [x] request logging
- [x] audit logging
- [x] support bundle export
- [ ] external error tracking
- [ ] metrics backend

## Delivery
- [x] CI gate scaffold
- [x] baseline snapshot on green
- [x] env separation scaffold
- [ ] protected branch settings applied in repo host
- [ ] deployment secrets configured

## Runbooks
- [x] operations
- [x] disaster recovery
- [x] deployment
- [x] admin

## Final gates before enterprise production
- [ ] staging environment live
- [ ] production environment live
- [ ] end-to-end suite expanded
- [ ] load test complete
- [ ] security review complete
- [ ] SLA/SLO defined
