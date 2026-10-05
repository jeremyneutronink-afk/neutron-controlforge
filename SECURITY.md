# Security Policy

Neutron ControlForge is security-sensitive software.

## Secret handling

Never commit:

- `.env`
- `.env.production`
- `apps/dashboard/.env.local`
- raw agent keys
- the administrative key
- database backups

If a secret is accidentally committed, uploaded, screenshotted, or shared,
rotate it.

## Vulnerability reports

Include the affected version, endpoint/component, reproduction steps, expected
behavior, actual behavior, impact, and remediation idea if known.

Do not include real customer secrets or production data.

See `docs/THREAT_MODEL.md` and `docs/ARCHITECTURE.md`.
