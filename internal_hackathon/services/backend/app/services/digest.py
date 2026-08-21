"""Officer/district email digest.

Aggregates the officer-facing case queue by district and emails a summary to
the configured officer recipients. This is the **officer** email channel — it
never contacts farmers by email (Module 9: email is officers-only).

Content is identity-light: it reports counts, bands, and SLA state, never
farmer phone numbers or other contact PII.
"""

from __future__ import annotations

from datetime import UTC, datetime
from html import escape

import structlog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.email import BaseEmailProvider, EmailProviderError, build_email_provider
from app.models.case import AlertCase
from app.models.geo import Village

logger = structlog.get_logger()

_OPEN_STATUSES = ("new", "acknowledged", "visited", "referred")


def _village_to_district(db: Session) -> dict[str, str]:
    # The villages table is PostGIS-only; it is absent in the SQLite fixture
    # database. Degrade to "unassigned" rather than failing the whole digest.
    try:
        return {row.village_id: (row.district_id or "unassigned") for row in db.query(Village).all()}
    except SQLAlchemyError:
        db.rollback()
        return {}


def build_district_digest(db: Session, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    village_district = _village_to_district(db)
    open_cases = (
        db.query(AlertCase)
        .filter(AlertCase.status.in_(_OPEN_STATUSES))
        .all()
    )

    districts: dict[str, dict] = {}
    for case in open_cases:
        district = village_district.get(case.village_id or "", "unassigned")
        bucket = districts.setdefault(
            district,
            {"district_id": district, "open": 0, "red": 0, "amber": 0, "green": 0, "sla_breached": 0},
        )
        bucket["open"] += 1
        band = str(case.band or "green").lower()
        bucket[band] = bucket.get(band, 0) + 1
        if str(case.sla_breached).lower() == "true":
            bucket["sla_breached"] += 1

    ordered = sorted(districts.values(), key=lambda item: (-item["red"], -item["open"], item["district_id"]))
    totals = {
        "open": sum(item["open"] for item in ordered),
        "red": sum(item["red"] for item in ordered),
        "amber": sum(item["amber"] for item in ordered),
        "sla_breached": sum(item["sla_breached"] for item in ordered),
    }
    return {"generated_at": now.isoformat(), "totals": totals, "districts": ordered}


def render_digest(summary: dict) -> tuple[str, str, str]:
    totals = summary["totals"]
    date_label = summary["generated_at"][:10]
    subject = f"KisanSetu officer digest {date_label} — {totals['red']} red, {totals['open']} open"

    lines = [
        f"KisanSetu officer digest — {date_label}",
        "",
        f"Open cases: {totals['open']}   Red: {totals['red']}   Amber: {totals['amber']}   SLA breached: {totals['sla_breached']}",
        "",
        "By district:",
    ]
    rows_html = []
    for item in summary["districts"]:
        lines.append(
            f"  - {item['district_id']}: {item['open']} open "
            f"({item['red']} red, {item['amber']} amber, {item['sla_breached']} SLA breached)"
        )
        rows_html.append(
            "<tr>"
            f"<td>{escape(item['district_id'])}</td>"
            f"<td style='text-align:right'>{item['open']}</td>"
            f"<td style='text-align:right;color:#b91c1c'>{item['red']}</td>"
            f"<td style='text-align:right;color:#b45309'>{item['amber']}</td>"
            f"<td style='text-align:right'>{item['sla_breached']}</td>"
            "</tr>"
        )
    if not summary["districts"]:
        lines.append("  (no open cases)")

    html = (
        f"<h2>KisanSetu officer digest — {escape(date_label)}</h2>"
        f"<p><strong>{totals['open']}</strong> open · "
        f"<strong style='color:#b91c1c'>{totals['red']}</strong> red · "
        f"<strong style='color:#b45309'>{totals['amber']}</strong> amber · "
        f"{totals['sla_breached']} SLA breached</p>"
        "<table cellpadding='6' style='border-collapse:collapse'>"
        "<tr><th align='left'>District</th><th>Open</th><th>Red</th><th>Amber</th><th>SLA</th></tr>"
        + "".join(rows_html)
        + "</table>"
        "<p style='color:#64748b;font-size:12px'>Identity-light summary. Open the officer dashboard to action individual cases.</p>"
    )
    return subject, "\n".join(lines), html


def send_district_digests(
    db: Session,
    *,
    now: datetime | None = None,
    provider: BaseEmailProvider | None = None,
) -> dict:
    recipients = settings.district_digest_recipient_list
    if not recipients:
        logger.info("district_digest_skipped_no_recipients")
        return {"sent": False, "reason": "no_recipients", "recipients": 0}

    summary = build_district_digest(db, now=now)
    subject, text, html = render_digest(summary)
    provider = provider or build_email_provider(settings)
    try:
        result = provider.send(to=recipients, subject=subject, text=text, html=html)
    except EmailProviderError as exc:
        logger.error("district_digest_send_failed", error=str(exc))
        return {"sent": False, "reason": str(exc), "recipients": len(recipients)}

    logger.info("district_digest_sent", provider=result.provider, recipients=len(result.accepted), totals=summary["totals"])
    return {"sent": True, "provider": result.provider, "recipients": len(result.accepted), "totals": summary["totals"]}
