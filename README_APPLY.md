# Apply the Neutron ControlForge V0.1 Release Bundle

This is the final release-hardening pass. It is intentionally additive and does
not replace the working API business logic.

## Adds

- Python SDK + example agent
- Python/SDK/health tests
- GitHub Actions CI
- API + dashboard Dockerfiles
- production Docker Compose
- secret generator + release-check script
- README, architecture, threat model, operations, security docs
- release checklist

## Replaces in full

- `.gitignore`
- `.env.example`
- `infra/docker-compose.yml`
- `apps/dashboard/next.config.ts`
- `apps/dashboard/package.json`

No database migration is included.

## Important: existing dev database

Before applying:

```powershell
docker volume ls | Select-String agentguard
```

The replacement dev Compose file pins the likely existing physical volume:

```text
neutron-agentguard_agentguard_postgres_data
```

If `docker volume ls` shows your real database volume has a different name,
change the `name:` field in `infra/docker-compose.yml` before starting Docker.

Do not delete the old volume simply because its internal name still says
`agentguard`.

## Apply

Extract/copy this bundle into:

```text
C:\Users\Jeremy\neutron-controlforge
```

preserving folders.

Then:

```powershell
cd C:\Users\Jeremy\neutron-controlforge
.\.venv\Scripts\Activate.ps1
pip install pytest
pip install -e sdk\python
```

The package.json change only adds the `typecheck` script, so no dependency or
lockfile update is required.

## Secret check

```powershell
git ls-files .env apps/dashboard/.env.local
```

If either is tracked:

```powershell
git rm --cached .env
git rm --cached apps/dashboard/.env.local
```

Then rotate any exposed secret.

## Verify

```powershell
python -c "from apps.api.app.main import app; print(app.title)"
alembic current
pytest tests -q
```

Then:

```powershell
cd apps\dashboard
npm run typecheck
npm run lint
npm run build
```

Or run the consolidated check:

```powershell
cd C:\Users\Jeremy\neutron-controlforge
.\scripts\release-check.ps1
```

## SDK smoke test

```powershell
$env:CONTROLFORGE_URL="http://127.0.0.1:8000"
$env:CONTROLFORGE_AGENT_ID="YOUR_AGENT_ID"
$env:CONTROLFORGE_AGENT_KEY="YOUR_AGENT_KEY"

python examples\python\basic_agent.py
```

## Production package smoke test

```powershell
Copy-Item .env.production.example .env.production
```

Replace both secrets, then:

```powershell
docker compose `
  --env-file .env.production `
  -f infra\docker-compose.prod.yml `
  config
```

Then build:

```powershell
docker compose `
  --env-file .env.production `
  -f infra\docker-compose.prod.yml `
  build
```

Once those are green, move through `RELEASE_CHECKLIST.md`.
