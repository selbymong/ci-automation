"""F081: Import JD Charities List (240 evaluated charities with detailed metrics).

Maps 94 columns to financial_analysis, srss_score, charity_rating, and sector tables.
Includes Q1-Q26 SRSS question responses and sector classifications.

Usage:
    python scripts/import/import_jd_charities.py [--excel PATH]

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
from app.models.charity import Charity  # noqa: E402
from app.models.financial_analysis import FinancialAnalysis  # noqa: E402
from app.models.rating import CharityRating  # noqa: E402
from app.models.sector import Sector, SectorGroup  # noqa: E402
from app.models.srss import SRSSScore, percentage_to_grade  # noqa: E402

DEFAULT_EXCEL = Path(__file__).resolve().parents[1] / "data" / "Charities_in_Process_2025.xlsx"
SHEET_NAME = "JD Charities List"

# SRSS question column mapping
SRSS_QUESTION_MAP = {f"Q{i}": f"q{i}" for i in range(1, 27)}

# SRSS category columns
SRSS_CATEGORY_MAP = {
    "Strategy %": "strategy_pct",
    "Activities %": "activities_pct",
    "Outputs %": "outputs_pct",
    "Outcomes %": "outcomes_pct",
    "Quality %": "quality_pct",
    "Learning %": "learning_pct",
    "SRSS Total %": "total_pct",
    "SRSS Grade": "letter_grade",
}

FINANCIAL_MAP = {
    "Total Revenue": "total_revenue",
    "Donations": "donations",
    "Government Funding": "government_funding",
    "Total Expenses": "total_expenses",
    "Program Costs": "program_costs",
    "Admin Costs": "admin_costs",
    "Fundraising Costs": "fundraising_costs",
    "Reserves": "reserves",
}

RATING_MAP = {
    "Star Rating": "star_rating",
    "Impact X": "impact_x",
    "Impact Y": "impact_y",
    "Impact Label": "impact_label",
    "Overhead %": "overhead_percent",
    "PCC": "program_cost_coverage",
}


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


def safe_str(val) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


async def import_from_records(records: list[dict], db: AsyncSession) -> dict:
    """Import JD Charities from pre-parsed records (dict-based, for testing)."""
    stats = {
        "charities_updated": 0, "charities_skipped": 0,
        "financials_created": 0, "srss_created": 0,
        "ratings_created": 0, "sectors_created": 0,
        "errors": 0,
    }

    for rec in records:
        cra = safe_str(rec.get("BN/Registration Number"))
        if not cra:
            stats["charities_skipped"] += 1
            continue

        try:
            # Find existing charity
            result = await db.execute(
                select(Charity).where(Charity.cra_number == cra)
            )
            charity = result.scalar_one_or_none()

            if charity is None:
                formal_name = safe_str(rec.get("Formal Name")) or f"Unknown ({cra})"
                charity = Charity(cra_number=cra, formal_name=formal_name)
                db.add(charity)
                await db.flush()

            # Update sector classification
            sector_name = safe_str(rec.get("Sector"))
            group_name = safe_str(rec.get("Sector Group"))
            if sector_name:
                charity.sector = sector_name
                # Create sector record if not exists
                result = await db.execute(
                    select(Sector).where(Sector.name == sector_name)
                )
                if not result.scalar_one_or_none():
                    group_id = None
                    if group_name:
                        grp_result = await db.execute(
                            select(SectorGroup).where(SectorGroup.name == group_name)
                        )
                        grp = grp_result.scalar_one_or_none()
                        if not grp:
                            grp = SectorGroup(name=group_name)
                            db.add(grp)
                            await db.flush()
                            stats["sectors_created"] += 1
                        group_id = grp.id
                    sector = Sector(name=sector_name, group_id=group_id)
                    db.add(sector)
                    stats["sectors_created"] += 1

            stats["charities_updated"] += 1

            # Import financial data
            fin_data = {}
            for excel_col, model_field in FINANCIAL_MAP.items():
                fin_data[model_field] = safe_float(rec.get(excel_col))
            has_fin = any(v is not None for v in fin_data.values())
            if has_fin:
                fye = safe_str(rec.get("Fiscal Year End"))
                fa = FinancialAnalysis(charity_id=charity.id, year_number=1, fiscal_year_end=fye or "N/A", **fin_data)
                total_exp = fa.total_expenses
                if total_exp and total_exp > 0:
                    fa.admin_percent = round((fa.admin_costs or 0) / total_exp * 100, 2)
                    fa.fundraising_percent = round((fa.fundraising_costs or 0) / total_exp * 100, 2)
                    fa.overhead_percent = round(fa.admin_percent + fa.fundraising_percent, 2)
                if fa.program_costs and fa.program_costs > 0 and fa.reserves is not None:
                    fa.program_cost_coverage = round(fa.reserves / fa.program_costs, 2)
                db.add(fa)
                stats["financials_created"] += 1

            # Import SRSS scores
            srss_data = {}
            for excel_col, model_field in SRSS_QUESTION_MAP.items():
                srss_data[model_field] = safe_int(rec.get(excel_col))
            for excel_col, model_field in SRSS_CATEGORY_MAP.items():
                if model_field == "letter_grade":
                    srss_data[model_field] = safe_str(rec.get(excel_col))
                else:
                    srss_data[model_field] = safe_float(rec.get(excel_col))

            has_srss = any(
                srss_data.get(f"q{i}") is not None for i in range(1, 27)
            )
            if has_srss:
                year = safe_int(rec.get("Year")) or 2025
                srss = SRSSScore(charity_id=charity.id, year=year, **srss_data)
                # Derive grade if not provided
                if not srss.letter_grade and srss.total_pct is not None:
                    srss.letter_grade = percentage_to_grade(srss.total_pct)
                db.add(srss)
                stats["srss_created"] += 1

            # Import rating
            rating_data = {}
            for excel_col, model_field in RATING_MAP.items():
                if model_field == "star_rating":
                    rating_data[model_field] = safe_int(rec.get(excel_col))
                elif model_field == "impact_label":
                    rating_data[model_field] = safe_str(rec.get(excel_col))
                else:
                    rating_data[model_field] = safe_float(rec.get(excel_col))
            has_rating = any(v is not None for v in rating_data.values())
            if has_rating:
                rating = CharityRating(charity_id=charity.id, **rating_data)
                db.add(rating)
                stats["ratings_created"] += 1

        except Exception as e:
            print(f"  Error importing {cra}: {e}")
            await db.rollback()
            stats["errors"] += 1

    await db.flush()
    return stats


async def import_from_excel(excel_path: Path) -> dict:
    """Import JD Charities List from Excel."""
    wb = openpyxl.load_workbook(str(excel_path), read_only=True, data_only=True)
    ws = wb[SHEET_NAME]

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return {"charities_updated": 0}

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
    parser = argparse.ArgumentParser(description="Import JD Charities List")
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
