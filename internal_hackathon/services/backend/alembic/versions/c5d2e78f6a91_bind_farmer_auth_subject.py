"""Bind opaque farmer resources to a Supabase Auth subject."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5d2e78f6a91"
down_revision: Union[str, Sequence[str], None] = "a13b8f4c2d10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("farmer_profiles", sa.Column("auth_subject", sa.String(), nullable=True))
    op.create_index("ix_farmer_profiles_auth_subject", "farmer_profiles", ["auth_subject"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_farmer_profiles_auth_subject", table_name="farmer_profiles")
    op.drop_column("farmer_profiles", "auth_subject")
