"""Add opt-in farmer email channel (encrypted email on the profile)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e9a1f7c2b8"
down_revision: Union[str, Sequence[str], None] = "7b71a8d2f4c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("farmer_profiles", sa.Column("email_enc", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("farmer_profiles", "email_enc")
