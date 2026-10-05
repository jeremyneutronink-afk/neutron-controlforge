import hashlib
import secrets

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from apps.api.app.core.config import get_settings
from apps.api.app.models import (
    Agent,
    SecurityAuditEvent,
)


AGENT_KEY_PREFIX = "agk_"


def generate_agent_api_key() -> str:
    return (
        AGENT_KEY_PREFIX
        + secrets.token_urlsafe(32)
    )


def hash_agent_api_key(
    api_key: str,
) -> str:
    return hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()


def agent_key_prefix(
    api_key: str,
) -> str:
    return api_key[:12]


def provision_agent_api_key(
    agent: Agent,
) -> str:
    raw_key = generate_agent_api_key()

    agent.api_key_hash = (
        hash_agent_api_key(
            raw_key
        )
    )

    agent.api_key_prefix = (
        agent_key_prefix(
            raw_key
        )
    )

    return raw_key


def write_security_audit_event(
    *,
    db: Session,
    event_type: str,
    severity: str,
    message: str,
    agent_id: str | None = None,
    event_data: dict | None = None,
) -> None:
    event = SecurityAuditEvent(
        agent_id=agent_id,
        event_type=event_type,
        severity=severity,
        message=message,
        event_data=event_data or {},
    )

    db.add(event)


def authenticate_agent(
    *,
    db: Session,
    agent_id: str,
    api_key: str | None,
) -> Agent:
    agent = db.get(
        Agent,
        agent_id,
    )

    if agent is None:
        write_security_audit_event(
            db=db,
            event_type="AGENT_AUTH_FAILED",
            severity="HIGH",
            message=(
                "Authentication attempted for an unknown agent."
            ),
            event_data={
                "claimed_agent_id": agent_id,
                "reason": "agent_not_found",
            },
        )

        db.commit()

        raise HTTPException(
            status_code=404,
            detail="Agent not found.",
        )

    if not agent.is_active:
        write_security_audit_event(
            db=db,
            event_type="AGENT_AUTH_FAILED",
            severity="HIGH",
            message=(
                "Inactive agent attempted to authenticate."
            ),
            agent_id=agent.id,
            event_data={
                "reason": "agent_inactive",
            },
        )

        db.commit()

        raise HTTPException(
            status_code=403,
            detail="Agent is inactive.",
        )

    if agent.api_key_hash is None:
        write_security_audit_event(
            db=db,
            event_type="AGENT_AUTH_FAILED",
            severity="MEDIUM",
            message=(
                "Agent attempted authentication before "
                "a credential was provisioned."
            ),
            agent_id=agent.id,
            event_data={
                "reason": "credential_not_provisioned",
            },
        )

        db.commit()

        raise HTTPException(
            status_code=401,
            detail=(
                "Agent does not have an API key. "
                "Provision a credential first."
            ),
        )

    if not api_key:
        write_security_audit_event(
            db=db,
            event_type="AGENT_AUTH_FAILED",
            severity="HIGH",
            message=(
                "Agent request was missing the X-Agent-Key header."
            ),
            agent_id=agent.id,
            event_data={
                "reason": "credential_missing",
            },
        )

        db.commit()

        raise HTTPException(
            status_code=401,
            detail="X-Agent-Key header is required.",
        )

    supplied_hash = (
        hash_agent_api_key(
            api_key
        )
    )

    if not secrets.compare_digest(
        supplied_hash,
        agent.api_key_hash,
    ):
        write_security_audit_event(
            db=db,
            event_type="AGENT_AUTH_FAILED",
            severity="HIGH",
            message=(
                "Agent authentication failed because "
                "the supplied credential was invalid."
            ),
            agent_id=agent.id,
            event_data={
                "reason": "invalid_credential",
                "credential_prefix": api_key[:12],
            },
        )

        db.commit()

        raise HTTPException(
            status_code=401,
            detail="Invalid agent credential.",
        )

    write_security_audit_event(
        db=db,
        event_type="AGENT_AUTH_SUCCESS",
        severity="INFO",
        message="Agent successfully authenticated.",
        agent_id=agent.id,
        event_data={
            "credential_prefix": (
                agent.api_key_prefix
            ),
        },
    )

    # Do not commit here on success.
    #
    # Successful authentication normally belongs to a larger
    # API transaction. The caller will commit that transaction,
    # keeping the audit event atomic with the operation.

    return agent


def require_admin_key(
    x_admin_key: str | None = Header(
        default=None,
        alias="X-Admin-Key",
    ),
) -> None:
    settings = get_settings()

    if not x_admin_key:
        raise HTTPException(
            status_code=401,
            detail="X-Admin-Key header is required.",
        )

    if not secrets.compare_digest(
        x_admin_key,
        settings.agentguard_admin_key,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid administrator credential.",
        )