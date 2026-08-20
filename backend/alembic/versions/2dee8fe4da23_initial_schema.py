"""initial schema

Revision ID: 2dee8fe4da23
Revises: 
Create Date: 2026-08-20 16:28:52.445683

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '2dee8fe4da23' 
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "farmer_profiles",
        sa.Column("farmer_token", sa.String, primary_key=True),
        sa.Column("village_id", sa.String, nullable=False),
        sa.Column("locale", sa.String, nullable=False),
        sa.Column("crop", sa.String, nullable=False),
        sa.Column("sowing_date", sa.Date, nullable=False),
        sa.Column("irrigation_type", sa.String, nullable=False),
        sa.Column("area_band", sa.String, nullable=False),
        sa.Column("phone_enc", sa.String, nullable=False),
        sa.Column("consent_flags", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_farmer_profiles_village", "farmer_profiles", ["village_id"])

    op.create_table(
        "crop_cycles",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("farmer_token", sa.String, sa.ForeignKey("farmer_profiles.farmer_token"), nullable=False),
        sa.Column("crop", sa.String, nullable=False),
        sa.Column("sowing_date", sa.Date, nullable=False),
        sa.Column("stage", sa.String),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_crop_cycles_crop_date", "crop_cycles", ["crop", "sowing_date"])

    op.create_table(
        "weather_observations",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("village_id", sa.String, nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric", sa.String, nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("unit", sa.String, nullable=False),
        sa.Column("quality", sa.String, nullable=False),
        sa.Column("ttl_hours", sa.Integer, nullable=False),
        sa.Column("source", sa.String, nullable=False),
    )
    op.create_index("ix_weather_village", "weather_observations", ["village_id"])

    op.create_table(
        "market_quotes",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("commodity", sa.String, nullable=False),
        sa.Column("mandi_id", sa.String, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("modal_price", sa.Float, nullable=False),
        sa.Column("arrivals", sa.Float),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("quality", sa.String, nullable=False),
    )
    op.create_index("ix_market_commodity_mandi_date", "market_quotes", ["commodity", "mandi_id", "date"])

    op.create_table(
        "farmer_reports",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("farmer_token", sa.String, sa.ForeignKey("farmer_profiles.farmer_token"), nullable=False),
        sa.Column("event_type", sa.String, nullable=False),
        sa.Column("reported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("notes", sa.String),
    )

    op.create_table(
        "risk_events",
        sa.Column("event_id", sa.String, primary_key=True),
        sa.Column("farmer_token", sa.String, sa.ForeignKey("farmer_profiles.farmer_token"), nullable=False),
        sa.Column("village_id", sa.String, nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("band", sa.String, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("contributors", postgresql.JSONB, nullable=False),
        sa.Column("action_ids", postgresql.JSONB, server_default="[]"),
        sa.Column("model_version", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_risk_events_band", "risk_events", ["band"])
    op.create_index("ix_risk_events_village", "risk_events", ["village_id"])

    op.create_table(
        "action_cards",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("event_id", sa.String, sa.ForeignKey("risk_events.event_id"), nullable=False),
        sa.Column("action_type", sa.String, nullable=False),
        sa.Column("content", postgresql.JSONB, nullable=False),
        sa.Column("language", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alert_cases",
        sa.Column("case_id", sa.String, primary_key=True),
        sa.Column("event_id", sa.String, sa.ForeignKey("risk_events.event_id"), nullable=False),
        sa.Column("recipient_role", sa.String, nullable=False),
        sa.Column("channel", sa.String, nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("ack_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String, nullable=False, server_default="new"),
        sa.Column("resolution_code", sa.String),
        sa.Column("notes", sa.String),
    )
    op.create_index("ix_alert_cases_status", "alert_cases", ["status"])

    op.create_table(
        "case_status_history",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("case_id", sa.String, sa.ForeignKey("alert_cases.case_id"), nullable=False),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("changed_by", sa.String),
    )

    op.create_table(
        "consents",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("farmer_token", sa.String, sa.ForeignKey("farmer_profiles.farmer_token"), nullable=False),
        sa.Column("store_data", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("allow_contact", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("allow_analytics", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("actor", sa.String, nullable=False),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("target_type", sa.String, nullable=False),
        sa.Column("target_id", sa.String, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metadata", postgresql.JSONB),
    )

    op.create_table(
        "scheme_chunks",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("scheme_name", sa.String, nullable=False),
        sa.Column("chunk_text", sa.String, nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float)),  # will alter to vector type below
        sa.Column("source_url", sa.String),
    )
    op.execute("ALTER TABLE scheme_chunks ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")
    op.execute("CREATE INDEX ix_scheme_chunks_embedding ON scheme_chunks USING ivfflat (embedding vector_cosine_ops)")


def downgrade():
    op.drop_table("scheme_chunks")
    op.drop_table("audit_events")
    op.drop_table("consents")
    op.drop_table("case_status_history")
    op.drop_table("alert_cases")
    op.drop_table("action_cards")
    op.drop_table("risk_events")
    op.drop_table("farmer_reports")
    op.drop_table("market_quotes")
    op.drop_table("weather_observations")
    op.drop_table("crop_cycles")
    op.drop_table("farmer_profiles")