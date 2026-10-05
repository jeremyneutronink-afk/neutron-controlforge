# ControlForge Operations

## Secrets

Never commit `.env`, `.env.production`, or `apps/dashboard/.env.local`.

Generate an admin secret:

```powershell
.\scripts\generate-admin-key.ps1
```

Use the same `AGENTGUARD_ADMIN_KEY` for API and dashboard server.

## Migrations

```powershell
alembic upgrade head
alembic current
```

Alembic is the schema owner.

## Development database after rename

The old repository directory was `neutron-agentguard`. Docker Compose normally
uses the directory name in its physical volume name. The development Compose
file explicitly pins:

```text
neutron-agentguard_agentguard_postgres_data
```

so the repo rename does not make your existing database appear empty.

Before deleting any old Docker volume, verify where your real data lives:

```powershell
docker volume ls | Select-String agentguard
```

## Production startup

```powershell
Copy-Item .env.production.example .env.production
# Replace both secrets.

docker compose `
  --env-file .env.production `
  -f infra\docker-compose.prod.yml `
  up -d --build
```

## Backup

```powershell
docker compose `
  --env-file .env.production `
  -f infra\docker-compose.prod.yml `
  exec -T postgres `
  pg_dump -U controlforge -d controlforge `
  > controlforge-backup.sql
```

Treat backups as sensitive.

## Restore

```powershell
Get-Content controlforge-backup.sql |
docker compose `
  --env-file .env.production `
  -f infra\docker-compose.prod.yml `
  exec -T postgres `
  psql -U controlforge -d controlforge
```

## Logs

```powershell
docker compose `
  --env-file .env.production `
  -f infra\docker-compose.prod.yml `
  logs -f api dashboard
```

Never log raw agent or admin credentials.

## Credential rotation

Agent key rotation invalidates the previous key immediately.

When rotating the admin secret, update API and dashboard runtime environments
together and restart both services.
