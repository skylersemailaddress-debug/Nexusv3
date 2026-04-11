# Nexus V3 Environments and Deployment Discipline

## Environments
- dev
- staging
- production

## Current configuration files
- env/.env.example
- env/.env.dev
- env/.env.staging
- env/.env.production

## Deployment scaffolding
- deploy/docker-compose.dev.yml
- deploy/nginx.staging.conf

## Rules
- dev uses local SQLite and local origins
- staging and production use managed Postgres target path
- staging and production assume reverse proxy + TLS
- promotion remains human-controlled until later phase

## Remaining deployment work after this step
- real Dockerfiles
- managed database provisioning
- secret injection from CI/CD
- domain/TLS provisioning
- production asset serving strategy
- worker/background process definition
