"""Persist SLA breach and resolution timestamps for durable case policy."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b71a8d2f4c1"
down_revision: Union[str, Sequence[str], None] = "c5d2e78f6a91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alert_cases", sa.Column("sla_breached", sa.String(), nullable=False, server_default="false"))
    op.add_column("alert_cases", sa.Column("sla_breached_at", sa.DateTime(), nullable=True))
    op.add_column("alert_cases", sa.Column("resolved_at", sa.DateTime(), nullable=True))
    op.create_index("ix_alert_cases_sla_queue", "alert_cases", ["status", "band", "sla_breached", "sla_due_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_alert_cases_sla_queue", table_name="alert_cases")
    op.drop_column("alert_cases", "resolved_at")
    op.drop_column("alert_cases", "sla_breached_at")
    op.drop_column("alert_cases", "sla_breached")
