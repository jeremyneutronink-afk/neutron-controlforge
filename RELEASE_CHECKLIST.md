# Neutron ControlForge V0.1 Release Checklist

## Source and secrets
- [ ] Repository is named `neutron-controlforge`
- [ ] `.env` is not tracked
- [ ] `apps/dashboard/.env.local` is not tracked
- [ ] Admin key is rotated after any accidental exposure
- [ ] No real secrets are present in the release commit

## Database
- [ ] PostgreSQL starts healthy
- [ ] Fresh database reaches Alembic head
- [ ] Existing development data remains after repo rename
- [ ] `alembic current` reports head

## Security
- [ ] Policy suite produces expected results
- [ ] System suite reports 10/10
- [ ] Cross-agent access is rejected
- [ ] Approval bypass is rejected
- [ ] Denied action cannot execute
- [ ] Completed run rejects mutation
- [ ] Old rotated key is rejected
- [ ] Operator endpoints require admin auth

## Product workflow
- [ ] Register agent
- [ ] Save one-time agent credential
- [ ] Create run
- [ ] Evaluate/execute allowed action
- [ ] Exercise approval-required action
- [ ] Resolve approval
- [ ] Complete run
- [ ] Run policy assessment
- [ ] Run system assessment
- [ ] Review/create finding
- [ ] Retest finding
- [ ] Generate report
- [ ] Export JSON
- [ ] Print/save report as PDF

## SDK / verification
- [ ] `pip install -e sdk/python` succeeds
- [ ] Example agent succeeds
- [ ] `pytest tests -q` passes
- [ ] Dashboard typecheck passes
- [ ] Dashboard lint passes
- [ ] Dashboard production build passes
- [ ] GitHub Actions is green

## Production package
- [ ] Production Compose config validates
- [ ] API healthcheck passes
- [ ] Dashboard loads
- [ ] PostgreSQL is not public
- [ ] Real secrets replace examples
- [ ] TLS/private-network boundary is planned

## Release
- [ ] README matches tested steps
- [ ] Architecture/threat model are current
- [ ] Known limitations are explicit
- [ ] Tag `v0.1.0`
