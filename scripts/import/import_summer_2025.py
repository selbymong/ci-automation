"""F082: Import Summer 2025 work-in-progress state.

Maps evaluation pipeline status to 12-stage state machine, imports analyst
assignments, priority scores, notes, outreach status, and financial acquisition state.

Usage:
    python scripts/import/import_summer_2025.py [--excel PATH]

Requires: openpyxl
"""
import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

import openpyxl  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.config import settings  # noqa: E402
from app.models.assignment import EvaluationAssignment  # noqa: E402
from app.models.charity import Charity  # noqa: E402
from app.models.cycle import EvaluationCycle  # noqa: E402
from app.models.evaluation import Evaluation, EvaluationStage  # noqa: E402
from app.models.financial_acquisition import FinancialAcquisition  # noqa: E402
from app.models.note import EvaluationNote  # noqa: E402
from app.models.outreach import CharityOutreach  # noqa: E402
from app.models.priority import PriorityScore  # noqa: E402
from app.models.user import User  # noqa: E402

DEFAULT_EXCEL = Path(__file__).resolve().parents[1] / "data" / "Charities_in_Process_2025.xlsx"
SHEET_NAME = "Summer 2025"

# Map from Excel status column values to evaluation stages
STATUS_STAGE_MAP = {
    "prioritized": EvaluationStage.prioritized,
    "assigned": EvaluationStage.assigned,
    "financials requested": EvaluationStage.financials_acquisition,
    "financials acquisition": EvaluationStage.financials_acquisition,
    "federal corp check": EvaluationStage.federal_corp_check,
    "cra data pull": EvaluationStage.cra_data_pull,
    "financial analysis": EvaluationStage.financial_analysis,
    "srss scoring": EvaluationStage.srss_scoring,
    "impact scoring": EvaluationStage.impact_scoring,
    "review": EvaluationStage.review,
    "outreach": EvaluationStage.charity_outreach,
    "charity outreach": EvaluationStage.charity_outreach,
    "charity response": EvaluationStage.charity_response,
    "published": EvaluationStage.published,
    "done": EvaluationStage.published,
    "complete": EvaluationStage.published,
}

# Note type columns
NOTE_COLUMNS = {
    "Notes": "general",
    "General Notes": "general",
    "Financial Notes": "financial",
    "Follow-up Notes": "followup",
    "Difficulty Notes": "difficulty",
}


def safe_str(val) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def safe_float(val) -> Optional[float]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_int(val) -> Optional[int]:
    if val is None or val == "" or val == "N/A":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def map_status_to_stage(status_value: Optional[str]) -> str:
    """Map Excel status text to evaluation stage enum."""
    if not status_value:
        return EvaluationStage.prioritized.value
    normalized = status_value.strip().lower()
    stage = STATUS_STAGE_MAP.get(normalized)
    if stage:
        return stage.value
    return EvaluationStage.prioritized.value


async def import_from_records(
    records: list[dict],
    db: AsyncSession,
    cycle_name: str = "Summer 2025",
    system_user_id: Optional[str] = None,
) -> dict:
    """Import Summer 2025 records from pre-parsed dicts."""
    stats = {
        "evaluations_created": 0, "assignments_created": 0,
        "notes_created": 0, "outreach_created": 0,
        "acquisitions_created": 0, "priorities_created": 0,
        "skipped": 0, "errors": 0,
    }

    # Get or create cycle
    result = await db.execute(
        select(EvaluationCycle).where(EvaluationCycle.name == cycle_name)
    )
    cycle = result.scalar_one_or_none()
    if not cycle:
        cycle = EvaluationCycle(name=cycle_name)
        db.add(cycle)
        await db.flush()

    # Cache analyst users by name
    analyst_cache: dict[str, str] = {}

    for rec in records:
        cra = safe_str(rec.get("BN/Registration Number"))
        if not cra:
            stats["skipped"] += 1
            continue

        try:
            # Find charity
            result = await db.execute(
                select(Charity).where(Charity.cra_number == cra)
            )
            charity = result.scalar_one_or_none()
            if not charity:
                stats["skipped"] += 1
                continue

            # Map status to stage
            stage = map_status_to_stage(safe_str(rec.get("Status")))

            # Create evaluation
            evaluation = Evaluation(
                charity_id=charity.id,
                cycle_id=cycle.id,
                stage=stage,
            )
            db.add(evaluation)
            await db.flush()
            stats["evaluations_created"] += 1

            # Create assignment if analyst specified
            analyst_name = safe_str(rec.get("Analyst"))
            if analyst_name:
                analyst_id = analyst_cache.get(analyst_name)
                if not analyst_id:
                    result = await db.execute(
                        select(User).where(User.full_name == analyst_name)
                    )
                    analyst = result.scalar_one_or_none()
                    if analyst:
                        analyst_id = analyst.id
                        analyst_cache[analyst_name] = analyst_id

                if analyst_id:
                    assignment = EvaluationAssignment(
                        analyst_id=analyst_id,
                        charity_id=charity.id,
                        cycle_id=cycle.id,
                    )
                    db.add(assignment)
                    evaluation.analyst_id = analyst_id
                    stats["assignments_created"] += 1

            # Import notes
            author_id = system_user_id or (analyst_id if analyst_name and analyst_id else None)
            for col_name, note_type in NOTE_COLUMNS.items():
                note_text = safe_str(rec.get(col_name))
                if note_text and author_id:
                    note = EvaluationNote(
                        charity_id=charity.id,
                        cycle_id=cycle.id,
                        note_type=note_type,
                        content=note_text,
                        author_id=author_id,
                    )
                    db.add(note)
                    stats["notes_created"] += 1

            # Import outreach status
            profile_sent = safe_str(rec.get("Profile Sent")) or safe_str(rec.get("Outreach Sent"))
            response_received = safe_str(rec.get("Response Received")) or safe_str(rec.get("Charity Response"))
            if profile_sent or response_received:
                outreach = CharityOutreach(
                    evaluation_id=evaluation.id,
                    charity_id=charity.id,
                    email_saved=bool(profile_sent),
                    response_received=bool(response_received),
                )
                if response_received:
                    outreach.charity_adds_content = response_received
                db.add(outreach)
                stats["outreach_created"] += 1

            # Import financial acquisition status
            fin_status = safe_str(rec.get("Financial Status")) or safe_str(rec.get("AFS Status"))
            if fin_status:
                acq = FinancialAcquisition(
                    charity_id=charity.id,
                    cycle_id=cycle.id,
                    status=fin_status.lower().replace(" ", "_")[:30],
                )
                db.add(acq)
                stats["acquisitions_created"] += 1

            # Import priority score
            priority_val = safe_int(rec.get("Priority")) or safe_int(rec.get("Priority Score"))
            if priority_val is not None:
                priority = PriorityScore(
                    charity_id=charity.id,
                    composite_score=safe_float(rec.get("Composite Score")) or float(priority_val),
                    priority_rank=priority_val,
                )
                db.add(priority)
                stats["priorities_created"] += 1

        except Exception as e:
            print(f"  Error importing {cra}: {e}")
            await db.rollback()
            stats["errors"] += 1

    await db.flush()
    return stats


async def import_from_excel(excel_path: Path) -> dict:
    """Import Summer 2025 from Excel."""
    wb = openpyxl.load_workbook(str(excel_path), read_only=True, data_only=True)
    ws = wb[SHEET_NAME]

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return {"evaluations_created": 0}

    headers = [str(h).strip() if h else "" for h in rows[0]]
    records = []
    for row in rows[1:]:
        rec = {headers[i]: cell for i, cell in enumerate(row) if i < len(headers)}
        records.append(rec)

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        stats = await import_from_records(records, session)
        await session.commit()

    await engine.dispose()
    wb.close()
    return stats


async def main():
    parser = argparse.ArgumentParser(description="Import Summer 2025 data")
    parser.add_argument("--excel", type=Path, default=DEFAULT_EXCEL)
    args = parser.parse_args()

    if not args.excel.exists():
        print(f"Excel file not found: {args.excel}")
        sys.exit(1)

    print(f"Importing from: {args.excel}")
    stats = await import_from_excel(args.excel)
    print("Import complete:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
