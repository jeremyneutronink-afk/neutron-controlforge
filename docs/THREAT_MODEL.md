# Neutron ControlForge V0.1 Threat Model

## Security objective

An agent must not perform an action outside the authority assigned to its own
identity and current policy state. Operator-only authority stays separate from
agent authority, and security decisions leave reproducible evidence.

## Primary assets

- Agent API credentials
- Administrative control-plane credential
- Policy decisions and approval state
- Run/execution state
- Security audit history
- Assessment evidence
- Findings and reports
- PostgreSQL data

## Threats and V0.1 controls

| Threat | V0.1 control |
| --- | --- |
| Missing/invalid agent credential | Agent authentication + audit |
| Cross-agent impersonation | Credential checked against agent identity |
| Horizontal run access | Owner authentication |
| Changed-payload replay | Agent-scoped idempotency + request hash |
| Approval bypass | Blocked execution until operator resolution |
| Policy-denied execution | Execution state gate |
| Mutation after completion | Run lifecycle validation |
| Unauthorized approval | Admin-key protected operator endpoint |
| Old credential reuse | Rotation replaces stored hash immediately |
| Unknown action | Default-deny policy |
| Untrusted destructive request | Trust-boundary policy |
| Stored raw agent key theft | Only key hash/prefix persisted |

## Assumptions

- The host running ControlForge is trusted.
- Internet-facing deployments terminate TLS outside ControlForge.
- PostgreSQL is not directly exposed publicly.
- Secrets are supplied through environment/secret management.
- The V0.1 sandbox executor does not perform real production side effects.

## Known V0.1 limitations

### Single administrative secret
V0.1 uses one operator secret rather than named accounts, MFA, or RBAC. This is
acceptable for a self-hosted single-operator/small-team release, but it is not
the final enterprise identity model.

### No built-in TLS termination
Use a reverse proxy, ingress, VPN, or private network boundary.

### No distributed rate limiter
Use gateway/network rate limits for internet-facing deployments.

### Built-in deterministic policy catalog
The V0.1 policy engine is intentionally explicit. Organization-specific policy
configuration is future work.

### Assessment scope
The system suite validates core control-plane protections; it is not a complete
application-specific penetration test.

## Release rule

A failed security test is a product finding. Fix the control or explicitly
document the accepted risk; do not weaken the test simply to make it green.
