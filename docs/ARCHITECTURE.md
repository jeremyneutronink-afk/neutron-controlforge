# Neutron ControlForge Architecture

## Purpose

ControlForge is a self-hostable AI agent security control plane. External agents
submit proposed actions to ControlForge before execution. ControlForge evaluates
policy, creates approval gates when needed, records security evidence, and
supports adversarial assessment and reporting.

## Core request path

```text
External Agent
    |
    | X-Agent-Key
    v
ControlForge Agent API
    |
    +--> identity / ownership validation
    +--> idempotency validation
    +--> deterministic policy engine
    |
    +--> ALLOW ------------> execution gate READY
    +--> REQUIRE_APPROVAL -> human approval -> READY or DENIED
    +--> DENY -------------> execution blocked
    |
    v
PostgreSQL evidence + audit trail
```

## Operator path

```text
Dashboard
    |
    | server-side X-Admin-Key
    v
ControlForge operator APIs
    |
    +--> agents
    +--> runs / timeline
    +--> approvals
    +--> assessments
    +--> findings / retests
    +--> reports
    +--> security audit
```

The admin key is kept server-side by the Next.js application. It is not intended
to be exposed as a `NEXT_PUBLIC_*` variable.

## Components

### FastAPI API
Authentication, authorization, policy, lifecycle, approvals, execution,
assessments, findings, reporting, and audit evidence.

### PostgreSQL
System of record. Alembic owns schema changes.

### Policy engine
Deterministic and fail-closed. Unknown actions are denied.

### System security harness
Attacks the real HTTP service to verify authentication, isolation, replay,
approval, execution, lifecycle, and credential controls.

### Dashboard
Daily operator interface. Operator API calls use the admin secret server-side.

### Python SDK
Small wrapper around the agent-facing API; it does not bypass any ControlForge
security boundary.

## Trust boundaries

1. External agent -> ControlForge API
2. Browser -> ControlForge dashboard
3. Dashboard server -> ControlForge operator API
4. ControlForge API -> PostgreSQL
5. System test harness -> ControlForge HTTP boundary
6. ControlForge -> sandbox executor

## V0.1 deployment

The production Compose stack runs PostgreSQL, FastAPI, and Next.js as separate
services. PostgreSQL remains internal to the Compose network.
