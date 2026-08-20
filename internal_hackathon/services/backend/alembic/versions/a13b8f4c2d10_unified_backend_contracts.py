"""Unify backend contracts for FDI v2, consent, cases, and delivery."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a13b8f4c2d10"
down_revision: Union[str, Sequence[str], None] = "9de47203cf19"
branch_labels = None
depends_on = None


def _add(table: str, column: sa.Column) -> None:
    op.add_column(table, column)


def upgrade() -> None:
    # Existing prototype tables are extended rather than replaced, preserving
    # local data while converging all deployments on one API contract.
    for table, column in [
        ("farmer_profiles", sa.Column("secondary_crop", sa.String(), nullable=True)),
        ("farmer_profiles", sa.Column("schemes_enrolled", sa.JSON(), nullable=True)),
        ("farmer_profiles", sa.Column("institutional_access", sa.String(), nullable=True)),
        ("farmer_profiles", sa.Column("soil_retention", sa.String(), nullable=True)),
        ("farmer_profiles", sa.Column("created_at", sa.DateTime(), nullable=True)),
        ("farmer_profiles", sa.Column("updated_at", sa.DateTime(), nullable=True)),
        ("weather_observations", sa.Column("plot_grid", sa.String(), nullable=True)),
        ("weather_observations", sa.Column("farmer_token", sa.String(), nullable=True)),
        ("weather_observations", sa.Column("created_at", sa.DateTime(), nullable=True)),
        ("risk_events", sa.Column("evaluated_at", sa.DateTime(), nullable=True)),
        ("risk_events", sa.Column("disclaimer", sa.String(), nullable=True)),
        ("risk_events", sa.Column("context_flags", sa.JSON(), nullable=True)),
        ("alert_cases", sa.Column("farmer_token", sa.String(), nullable=True)),
        ("alert_cases", sa.Column("village_id", sa.String(), nullable=True)),
        ("alert_cases", sa.Column("band", sa.String(), nullable=True)),
        ("alert_cases", sa.Column("confidence", sa.Float(), nullable=True)),
        ("alert_cases", sa.Column("assigned_to", sa.String(), nullable=True)),
        ("alert_cases", sa.Column("sla_due_at", sa.DateTime(), nullable=True)),
        ("alert_cases", sa.Column("created_at", sa.DateTime(), nullable=True)),
        ("alert_cases", sa.Column("updated_at", sa.DateTime(), nullable=True)),
        ("outbox_messages", sa.Column("idempotency_key", sa.String(), nullable=True)),
        ("outbox_messages", sa.Column("farmer_token", sa.String(), nullable=True)),
        ("outbox_messages", sa.Column("consent_required", sa.String(), nullable=True)),
    ]:
        _add(table, column)
    if op.get_bind().dialect.name == "postgresql":
        op.alter_column(
            "weather_observations",
            "value",
            existing_type=sa.Float(),
            type_=sa.JSON(),
            postgresql_using="to_jsonb(value)",
        )
    op.create_index("ix_outbox_messages_idempotency_key", "outbox_messages", ["idempotency_key"], unique=True)
    op.create_index("ix_alert_cases_farmer_token", "alert_cases", ["farmer_token"], unique=False)
    op.create_index("ix_alert_cases_village_id", "alert_cases", ["village_id"], unique=False)
    op.create_index("ix_weather_observations_farmer_token", "weather_observations", ["farmer_token"], unique=False)

    op.create_table(
        "case_status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(), nullable=True),
        sa.Column("to_status", sa.String(), nullable=False),
        sa.Column("actor_id", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_case_status_history_case_id", "case_status_history", ["case_id"], unique=False)
    op.create_table(
        "delivery_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("provider_reference", sa.String(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_delivery_attempts_message_id", "delivery_attempts", ["message_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_delivery_attempts_message_id", table_name="delivery_attempts")
    op.drop_table("delivery_attempts")
    op.drop_index("ix_case_status_history_case_id", table_name="case_status_history")
    op.drop_table("case_status_history")
    op.drop_index("ix_alert_cases_village_id", table_name="alert_cases")
    op.drop_index("ix_alert_cases_farmer_token", table_name="alert_cases")
    op.drop_index("ix_weather_observations_farmer_token", table_name="weather_observations")
    op.drop_index("ix_outbox_messages_idempotency_key", table_name="outbox_messages")
    for table, name in [
        ("outbox_messages", "consent_required"),
        ("outbox_messages", "farmer_token"),
        ("outbox_messages", "idempotency_key"),
        ("alert_cases", "updated_at"),
        ("alert_cases", "created_at"),
        ("alert_cases", "sla_due_at"),
        ("alert_cases", "assigned_to"),
        ("alert_cases", "confidence"),
        ("alert_cases", "band"),
        ("alert_cases", "village_id"),
        ("alert_cases", "farmer_token"),
        ("risk_events", "context_flags"),
        ("risk_events", "disclaimer"),
        ("risk_events", "evaluated_at"),
        ("weather_observations", "created_at"),
        ("weather_observations", "farmer_token"),
        ("weather_observations", "plot_grid"),
        ("farmer_profiles", "updated_at"),
        ("farmer_profiles", "created_at"),
        ("farmer_profiles", "soil_retention"),
        ("farmer_profiles", "institutional_access"),
        ("farmer_profiles", "schemes_enrolled"),
        ("farmer_profiles", "secondary_crop"),
    ]:
        op.drop_column(table, name)
