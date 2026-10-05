"""add assessment run batching

Revision ID: b9e66e81a277
Revises: 9de8afffecf6
Create Date: 2026-10-01 17:59:22.099226

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b9e66e81a277"
down_revision: Union[str, Sequence[str], None] = "9de8afffecf6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SECURITY_TEST_FK_NAME = (
    "fk_security_test_results_assessment_run_id"
)

SYSTEM_TEST_FK_NAME = (
    "fk_system_security_test_results_assessment_run_id"
)


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "assessment_runs",
        sa.Column(
            "id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "assessment_type",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "scope_key",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "total",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "passed",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "failed",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
        ),
        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        op.f(
            "ix_assessment_runs_agent_id"
        ),
        "assessment_runs",
        ["agent_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_assessment_runs_assessment_type"
        ),
        "assessment_runs",
        ["assessment_type"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_assessment_runs_scope_key"
        ),
        "assessment_runs",
        ["scope_key"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_assessment_runs_started_at"
        ),
        "assessment_runs",
        ["started_at"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_assessment_runs_status"
        ),
        "assessment_runs",
        ["status"],
        unique=False,
    )

    op.add_column(
        "security_test_results",
        sa.Column(
            "assessment_run_id",
            sa.String(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f(
            "ix_security_test_results_assessment_run_id"
        ),
        "security_test_results",
        ["assessment_run_id"],
        unique=False,
    )

    op.create_foreign_key(
        SECURITY_TEST_FK_NAME,
        "security_test_results",
        "assessment_runs",
        ["assessment_run_id"],
        ["id"],
    )

    op.add_column(
        "system_security_test_results",
        sa.Column(
            "assessment_run_id",
            sa.String(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f(
            "ix_system_security_test_results_assessment_run_id"
        ),
        "system_security_test_results",
        ["assessment_run_id"],
        unique=False,
    )

    op.create_foreign_key(
        SYSTEM_TEST_FK_NAME,
        "system_security_test_results",
        "assessment_runs",
        ["assessment_run_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        SYSTEM_TEST_FK_NAME,
        "system_security_test_results",
        type_="foreignkey",
    )

    op.drop_index(
        op.f(
            "ix_system_security_test_results_assessment_run_id"
        ),
        table_name="system_security_test_results",
    )

    op.drop_column(
        "system_security_test_results",
        "assessment_run_id",
    )

    op.drop_constraint(
        SECURITY_TEST_FK_NAME,
        "security_test_results",
        type_="foreignkey",
    )

    op.drop_index(
        op.f(
            "ix_security_test_results_assessment_run_id"
        ),
        table_name="security_test_results",
    )

    op.drop_column(
        "security_test_results",
        "assessment_run_id",
    )

    op.drop_index(
        op.f(
            "ix_assessment_runs_status"
        ),
        table_name="assessment_runs",
    )

    op.drop_index(
        op.f(
            "ix_assessment_runs_started_at"
        ),
        table_name="assessment_runs",
    )

    op.drop_index(
        op.f(
            "ix_assessment_runs_scope_key"
        ),
        table_name="assessment_runs",
    )

    op.drop_index(
        op.f(
            "ix_assessment_runs_assessment_type"
        ),
        table_name="assessment_runs",
    )

    op.drop_index(
        op.f(
            "ix_assessment_runs_agent_id"
        ),
        table_name="assessment_runs",
    )

    op.drop_table(
        "assessment_runs"
    )