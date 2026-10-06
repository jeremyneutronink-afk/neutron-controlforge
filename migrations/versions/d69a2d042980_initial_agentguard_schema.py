"""initial agentguard schema

Revision ID: d69a2d042980
Revises:
Create Date: 2026-09-24 11:04:39.890516

This baseline migration creates the original ControlForge core schema.

Important:
- Agent API credential columns are intentionally NOT created here. They are
  added later by revision 018454b0573c.
- runs.completed_at and the runs.status index are intentionally NOT created
  here. They are added later by revision 06b709338611.
- Later migrations own security test results, findings, security audit events,
  system test results, and assessment runs.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d69a2d042980"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_runs_agent_id"), "runs", ["agent_id"], unique=False)

    op.create_table(
        "actions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("action_name", sa.String(length=120), nullable=False),
        sa.Column("resource", sa.String(length=255), nullable=True),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_actions_agent_id"), "actions", ["agent_id"], unique=False)
    op.create_index(op.f("ix_actions_run_id"), "actions", ["run_id"], unique=False)

    op.create_table(
        "decisions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("action_id", sa.String(), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("risk", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("policy", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["action_id"], ["actions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_decisions_action_id"), "decisions", ["action_id"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("event_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_agent_id"), "events", ["agent_id"], unique=False)
    op.create_index(op.f("ix_events_event_type"), "events", ["event_type"], unique=False)
    op.create_index(op.f("ix_events_run_id"), "events", ["run_id"], unique=False)

    op.create_table(
        "approvals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("action_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(length=120), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["action_id"], ["actions.id"]),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_approvals_action_id"), "approvals", ["action_id"], unique=True)
    op.create_index(op.f("ix_approvals_agent_id"), "approvals", ["agent_id"], unique=False)
    op.create_index(op.f("ix_approvals_run_id"), "approvals", ["run_id"], unique=False)
    op.create_index(op.f("ix_approvals_status"), "approvals", ["status"], unique=False)

    op.create_table(
        "executions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("action_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("executor", sa.String(length=100), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["action_id"], ["actions.id"]),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_executions_action_id"), "executions", ["action_id"], unique=True)
    op.create_index(op.f("ix_executions_agent_id"), "executions", ["agent_id"], unique=False)
    op.create_index(op.f("ix_executions_run_id"), "executions", ["run_id"], unique=False)
    op.create_index(op.f("ix_executions_status"), "executions", ["status"], unique=False)

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "idempotency_key", name="uq_idempotency_agent_key"),
    )
    op.create_index(op.f("ix_idempotency_records_agent_id"), "idempotency_records", ["agent_id"], unique=False)
    op.create_index(op.f("ix_idempotency_records_idempotency_key"), "idempotency_records", ["idempotency_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_idempotency_records_idempotency_key"), table_name="idempotency_records")
    op.drop_index(op.f("ix_idempotency_records_agent_id"), table_name="idempotency_records")
    op.drop_table("idempotency_records")

    op.drop_index(op.f("ix_executions_status"), table_name="executions")
    op.drop_index(op.f("ix_executions_run_id"), table_name="executions")
    op.drop_index(op.f("ix_executions_agent_id"), table_name="executions")
    op.drop_index(op.f("ix_executions_action_id"), table_name="executions")
    op.drop_table("executions")

    op.drop_index(op.f("ix_approvals_status"), table_name="approvals")
    op.drop_index(op.f("ix_approvals_run_id"), table_name="approvals")
    op.drop_index(op.f("ix_approvals_agent_id"), table_name="approvals")
    op.drop_index(op.f("ix_approvals_action_id"), table_name="approvals")
    op.drop_table("approvals")

    op.drop_index(op.f("ix_events_run_id"), table_name="events")
    op.drop_index(op.f("ix_events_event_type"), table_name="events")
    op.drop_index(op.f("ix_events_agent_id"), table_name="events")
    op.drop_table("events")

    op.drop_index(op.f("ix_decisions_action_id"), table_name="decisions")
    op.drop_table("decisions")

    op.drop_index(op.f("ix_actions_run_id"), table_name="actions")
    op.drop_index(op.f("ix_actions_agent_id"), table_name="actions")
    op.drop_table("actions")

    op.drop_index(op.f("ix_runs_agent_id"), table_name="runs")
    op.drop_table("runs")

    op.drop_table("agents")
