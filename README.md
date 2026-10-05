# Neutron ControlForge

**AI Agent Security Control Plane**

Neutron ControlForge is a self-hostable control and assessment platform for AI
agents. Agents submit proposed actions to ControlForge, which authenticates the
agent, evaluates deterministic policy, enforces approval/execution gates,
records evidence, runs adversarial tests, tracks findings, and generates reports.

## V0.1 capabilities

- Agent registration + one-time machine credentials
- Agent-isolated run lifecycle
- Fail-closed policy enforcement
- `ALLOW`, `DENY`, `REQUIRE_APPROVAL`
- Human approval gates
- Idempotent action evaluation
- Sandboxed execution
- Security/audit history
- Policy test packs
- HTTP-boundary system security suite
- Assessment batching/history
- Findings, remediation, retest
- Report view/print + JSON export
- Operator dashboard
- Python SDK
- Production Docker packaging
- CI + release checks

## Architecture

```text
External Agent
      |
      | X-Agent-Key
      v
+---------------------------+
| Neutron ControlForge API  |
| auth / ownership          |
| idempotency / policy      |
| approval / execution      |
+-------------+-------------+
              |
              v
          PostgreSQL
              ^
              |
+-------------+-------------+
| Operator Dashboard        |
| Assessments / Findings    |
| Approvals / Reports       |
+---------------------------+
```

See `docs/ARCHITECTURE.md` and `docs/THREAT_MODEL.md`.

## Local requirements

- Python 3.12 recommended
- Node.js 20+
- Docker Desktop

## Local setup

### PostgreSQL

```powershell
docker compose -f infra\docker-compose.yml up -d
docker compose -f infra\docker-compose.yml ps
```

The development Compose file preserves the database volume created before the
repository rename. Read `docs/OPERATIONS.md` before deleting old volumes.

### Backend

```powershell
Copy-Item .env.example .env
.\scripts\generate-admin-key.ps1
```

Put the generated value in `.env` as `AGENTGUARD_ADMIN_KEY`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r apps\api\requirements.txt
alembic upgrade head
uvicorn apps.api.app.main:app --reload
```

API: `http://127.0.0.1:8000`

Docs: `http://127.0.0.1:8000/docs`

### Dashboard

Create `apps/dashboard/.env.local`:

```env
AGENTGUARD_API_URL=http://127.0.0.1:8000
AGENTGUARD_ADMIN_KEY=the-same-admin-key-used-by-the-api
```

Then:

```powershell
cd apps\dashboard
npm ci
npm run dev
```

Dashboard: `http://localhost:3000`

`AGENTGUARD_*` remains the internal V0.1 environment namespace for backward
compatibility. The product name is Neutron ControlForge.

## Python SDK

```powershell
pip install -e sdk\python
```

Register an agent in the dashboard and save its one-time key, then:

```powershell
$env:CONTROLFORGE_URL="http://127.0.0.1:8000"
$env:CONTROLFORGE_AGENT_ID="your-agent-id"
$env:CONTROLFORGE_AGENT_KEY="your-agent-key"

python examples\python\basic_agent.py
```

## Verification

```powershell
pip install pytest
pip install -e sdk\python
pytest tests -q
```

Dashboard:

```powershell
cd apps\dashboard
npm run typecheck
npm run lint
npm run build
```

Or:

```powershell
.\scripts\release-check.ps1
```

## Production Compose

```powershell
Copy-Item .env.production.example .env.production
```

Replace both secrets, then:

```powershell
docker compose `
  --env-file .env.production `
  -f infra\docker-compose.prod.yml `
  up -d --build
```

Internet-facing deployments should sit behind TLS and an appropriate private
network, ingress, or API gateway.

## V0.1 security boundary

V0.1 uses per-agent credentials and one server-side operator admin secret.
Named operator accounts, MFA, fine-grained RBAC, and distributed rate limiting
are explicitly outside this release boundary.

See `SECURITY.md`, `docs/THREAT_MODEL.md`, and `RELEASE_CHECKLIST.md`.
