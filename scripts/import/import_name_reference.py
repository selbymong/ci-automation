"""F080: Import charity records from the Name Reference sheet.

Maps 175 columns across charity identity, financial, rating, and content fields.
Imports into: charity, financial_analysis, charity_rating, transparency_config,
profile_content, srss_score tables.

Usage:
    python scripts/import/import_name_reference.py [--excel PATH]

Requires: openpyxl
"""
import argparse
import asyncio
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

import openpyxl  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402
from app.models.charity import Charity  # noqa: E402
from app.models.financial_analysis import FinancialAnalysis  # noqa: E402
from app.models.rating import CharityRating  # noqa: E402
from app.models.transparency import TransparencyConfig, TRANSPARENCY_FLAGS  # noqa: E402
from app.models.profile_content import ProfileContent  # noqa: E402

DEFAULT_EXCEL = Path(__file__).resolve().parents[1] / "data" / "Charities_in_Process_2025.xlsx"
SHEET_NAME = "Name Reference"

# Charity identity columns
CHARITY_COLUMN_MAP = {
    "BN/Registration Number": "cra_number",
    "Formal Name": "formal_name",
    "Common Name": "common_name",
    "Sector": "sector",
    "Sub-Sector": "sub_sector",
    "Fiscal Year End": "fiscal_year_end",
    "Website": "website",
    "City": "city",
    "Province": "province",
}

# Financial data columns -> FinancialAnalysis fields
FINANCIAL_COLUMN_MAP = {
    "Total Revenue": "total_revenue",
    "Donations": "donations",
    "Government Funding": "government_funding",
    "Total Expenses": "total_expenses",
    "Program Costs": "program_costs",
    "Admin Costs": "admin_costs",
    "Fundraising Costs": "fundraising_costs",
    "Reserves": "reserves",
    "Assets": "total_assets",
    "Liabilities": "total_liabilities",
}

# Rating columns
RATING_COLUMN_MAP = {
    "Star Rating": "star_rating",
    "Impact X": "impact_x",
    "Impact Y": "impact_y",
    "Impact Label": "impact_label",
    "Admin %": "admin_percent",
    "Fundraising %": "fundraising_percent",
    "Overhead %": "overhead_percent",
    "PCC": "program_cost_coverage",
    "SRSS Score": "srss_score",
}

# Content sections
CONTENT_COLUMNS = {
    "Results and Impact": "results_impact",
    "ResultsAndImpact": "results_impact",
    "Mission": "mission",
    "Financial Review": "financial_review",
    "Financial Notes": "financial_notes",
    "AndTheCharityAdds": "charity_adds",
    "Charity Adds": "charity_adds",
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


def safe_date(val) -> Optional[date]:
    if val is None or val == "" or val == "N/A":
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val).strip()[:10])
    except (ValueError, TypeError):
        return None


def safe_str(val) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def parse_charity(headers: list[str], row: tuple) -> Optional[dict]:
    """Parse charity identity fields from a row."""
    raw = {headers[i]: cell for i, cell in enumerate(row) if i < len(headers)}
    cra = raw.get("BN/Registration Number")
    formal = raw.get("Formal Name")
    if not cra or not formal:
        return None

    record = {}
    for excel_col, model_field in CHARITY_COLUMN_MAP.items():
        value = raw.get(excel_col)
        if model_field == "fiscal_year_end":
            record[model_field] = safe_date(value)
        else:
            record[model_field] = safe_str(value)

    record["cra_number"] = str(record["cra_number"]).strip()
    record["formal_name"] = str(record["formal_name"]).strip()

    top100 = raw.get("Top 100") or raw.get("Top100")
    record["is_top_100"] = bool(top100) if top100 else False

    return record


def parse_financials(headers: list[str], row: tuple) -> dict:
    """Parse financial fields from a row."""
    raw = {headers[i]: cell for i, cell in enumerate(row) if i < len(headers)}
    record = {}
    for excel_col, model_field in FINANCIAL_COLUMN_MAP.items():
        record[model_field] = safe_float(raw.get(excel_col))
    return record


def parse_rating(headers: list[str], row: tuple) -> dict:
    """Parse rating fields from a row."""
    raw = {headers[i]: cell for i, cell in enumerate(row) if i < len(headers)}
    record = {}
    for excel_col, model_field in RATING_COLUMN_MAP.items():
        if model_field == "star_rating":
            record[model_field] = safe_int(raw.get(excel_col))
        elif model_field == "impact_label":
            record[model_field] = safe_str(raw.get(excel_col))
        else:
            record[model_field] = safe_float(raw.get(excel_col))
    return record


def parse_content(headers: list[str], row: tuple) -> dict[str, str]:
    """Parse profile content fields from a row."""
    raw = {headers[i]: cell for i, cell in enumerate(row) if i < len(headers)}
    sections = {}
    for excel_col, section_type in CONTENT_COLUMNS.items():
        val = safe_str(raw.get(excel_col))
        if val and section_type not in sections:
            sections[section_type] = val
    return sections


def parse_transparency(headers: list[str], row: tuple) -> dict:
    """Parse transparency flag columns."""
    raw = {headers[i]: cell for i, cell in enumerate(row) if i < len(headers)}
    flags = {}
    for flag in TRANSPARENCY_FLAGS:
        # Try both REPORT_Show format and clean format
        for prefix in ["REPORT_Show", "Show_", ""]:
            key = f"{prefix}{flag.replace('show_', '')}"
            val = raw.get(key)
            if val is not None:
                flags[flag] = bool(val)
                break
    return flags


async def import_from_excel(excel_path: Path) -> dict:
    """Import all Name Reference data. Returns stats dict."""
    wb = openpyxl.load_workbook(str(excel_path), read_only=True, data_only=True)
    ws = wb[SHEET_NAME]

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return {"charities_created": 0, "skipped": 0, "errors": 0}

    headers = [str(h).strip() if h else "" for h in rows[0]]
    data_rows = rows[1:]

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    stats = {
        "charities_created": 0, "charities_skipped": 0,
        "financials_created": 0, "ratings_created": 0,
        "content_created": 0, "errors": 0,
    }

    async with session_factory() as session:
        for row in data_rows:
            charity_data = parse_charity(headers, row)
            if charity_data is None:
                stats["charities_skipped"] += 1
                continue

            try:
                # Check if charity exists
                existing = await session.execute(
                    select(Charity).where(Charity.cra_number == charity_data["cra_number"])
                )
                charity = existing.scalar_one_or_none()

                if charity is None:
                    charity = Charity(**charity_data)
                    session.add(charity)
                    await session.flush()
                    stats["charities_created"] += 1
                else:
                    stats["charities_skipped"] += 1

                # Import financials if data present
                fin_data = parse_financials(headers, row)
                has_fin = any(v is not None for v in fin_data.values())
                if has_fin:
                    raw = {headers[i]: cell for i, cell in enumerate(row) if i < len(headers)}
                    fye = safe_str(raw.get("Fiscal Year End"))
                    fa = FinancialAnalysis(
                        charity_id=charity.id,
                        year_number=1,
                        fiscal_year_end=fye or "N/A",
                        **fin_data,
                    )
                    # Calculate derived metrics
                    total_exp = fa.total_expenses
                    if total_exp and total_exp > 0:
                        fa.admin_percent = round((fa.admin_costs or 0) / total_exp * 100, 2)
                        fa.fundraising_percent = round((fa.fundraising_costs or 0) / total_exp * 100, 2)
                        fa.overhead_percent = round(fa.admin_percent + fa.fundraising_percent, 2)
                    if fa.program_costs and fa.program_costs > 0 and fa.reserves is not None:
                        fa.program_cost_coverage = round(fa.reserves / fa.program_costs, 2)
                    session.add(fa)
                    stats["financials_created"] += 1

                # Import rating
                rating_data = parse_rating(headers, row)
                has_rating = any(v is not None for v in rating_data.values())
                if has_rating:
                    rating = CharityRating(charity_id=charity.id, **rating_data)
                    session.add(rating)
                    stats["ratings_created"] += 1

                # Import content sections
                content = parse_content(headers, row)
                for section_type, text in content.items():
                    pc = ProfileContent(
                        charity_id=charity.id,
                        section_type=section_type,
                        content=text,
                        version=1,
                    )
                    session.add(pc)
                    stats["content_created"] += 1

            except Exception as e:
                print(f"  Error importing {charity_data.get('cra_number')}: {e}")
                stats["errors"] += 1

        await session.commit()

    await engine.dispose()
    wb.close()
    return stats


async def import_from_records(records: list[dict], db: AsyncSession) -> dict:
    """Import from pre-parsed records (for testing without Excel).

    Each record should have keys matching column headers.
    """
    stats = {
        "charities_created": 0, "charities_skipped": 0,
        "financials_created": 0, "ratings_created": 0,
        "content_created": 0, "errors": 0,
    }

    headers = list(records[0].keys()) if records else []

    for rec in records:
        row = tuple(rec.get(h) for h in headers)
        charity_data = parse_charity(headers, row)
        if charity_data is None:
            stats["charities_skipped"] += 1
            continue

        try:
            existing = await db.execute(
                select(Charity).where(Charity.cra_number == charity_data["cra_number"])
            )
            charity = existing.scalar_one_or_none()

            if charity is None:
                charity = Charity(**charity_data)
                db.add(charity)
                await db.flush()
                stats["charities_created"] += 1
            else:
                stats["charities_skipped"] += 1

            fin_data = parse_financials(headers, row)
            has_fin = any(v is not None for v in fin_data.values())
            if has_fin:
                fye = safe_str(rec.get("Fiscal Year End"))
                fa = FinancialAnalysis(
                    charity_id=charity.id,
                    year_number=1,
                    fiscal_year_end=fye or "N/A",
                    **fin_data,
                )
                total_exp = fa.total_expenses
                if total_exp and total_exp > 0:
                    fa.admin_percent = round((fa.admin_costs or 0) / total_exp * 100, 2)
                    fa.fundraising_percent = round((fa.fundraising_costs or 0) / total_exp * 100, 2)
                    fa.overhead_percent = round(fa.admin_percent + fa.fundraising_percent, 2)
                if fa.program_costs and fa.program_costs > 0 and fa.reserves is not None:
                    fa.program_cost_coverage = round(fa.reserves / fa.program_costs, 2)
                db.add(fa)
                stats["financials_created"] += 1

            rating_data = parse_rating(headers, row)
            has_rating = any(v is not None for v in rating_data.values())
            if has_rating:
                rating = CharityRating(charity_id=charity.id, **rating_data)
                db.add(rating)
                stats["ratings_created"] += 1

            content = parse_content(headers, row)
            for section_type, text in content.items():
                pc = ProfileContent(
                    charity_id=charity.id,
                    section_type=section_type,
                    content=text,
                    version=1,
                )
                db.add(pc)
                stats["content_created"] += 1

        except Exception as e:
            print(f"  Error importing {charity_data.get('cra_number')}: {e}")
            await db.rollback()
            stats["errors"] += 1

    await db.flush()
    return stats


async def main():
    parser = argparse.ArgumentParser(description="Import Name Reference charities")
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
