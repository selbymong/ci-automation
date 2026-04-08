"""Import charity records from the Name Reference sheet of the CI workbook.

Usage:
    python scripts/import/import_name_reference.py [--excel PATH]

Requires: openpyxl
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

import openpyxl  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402
from app.models.charity import Charity  # noqa: E402

DEFAULT_EXCEL = Path(__file__).resolve().parents[1] / "data" / "Charities_in_Process_2025.xlsx"
SHEET_NAME = "Name Reference"

# Column mapping: Excel column header -> Charity model field
COLUMN_MAP = {
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


def parse_row(headers: list[str], row: tuple) -> dict | None:
    """Convert an Excel row to a dict of Charity fields."""
    raw = {headers[i]: cell for i, cell in enumerate(row) if i < len(headers)}

    cra = raw.get("BN/Registration Number")
    formal = raw.get("Formal Name")
    if not cra or not formal:
        return None

    record = {}
    for excel_col, model_field in COLUMN_MAP.items():
        value = raw.get(excel_col)
        if value is not None:
            record[model_field] = str(value).strip() if isinstance(value, str) else value
        else:
            record[model_field] = None

    # Ensure cra_number and formal_name are strings
    record["cra_number"] = str(record["cra_number"]).strip()
    record["formal_name"] = str(record["formal_name"]).strip()

    # Check for Top 100 column if present
    top100 = raw.get("Top 100") or raw.get("Top100")
    record["is_top_100"] = bool(top100) if top100 else False

    return record


async def import_from_excel(excel_path: Path) -> tuple[int, int, int]:
    """Import charities from Excel. Returns (created, skipped, errors)."""
    wb = openpyxl.load_workbook(str(excel_path), read_only=True, data_only=True)
    ws = wb[SHEET_NAME]

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return 0, 0, 0

    headers = [str(h).strip() if h else "" for h in rows[0]]
    data_rows = rows[1:]

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    created = 0
    skipped = 0
    errors = 0

    async with session_factory() as session:
        for row in data_rows:
            record = parse_row(headers, row)
            if record is None:
                skipped += 1
                continue

            try:
                existing = await session.execute(
                    select(Charity).where(Charity.cra_number == record["cra_number"])
                )
                if existing.scalar_one_or_none() is not None:
                    skipped += 1
                    continue

                charity = Charity(**record)
                session.add(charity)
                await session.flush()
                created += 1
            except Exception as e:
                print(f"  Error importing {record.get('cra_number')}: {e}")
                errors += 1

        await session.commit()

    await engine.dispose()
    wb.close()
    return created, skipped, errors


async def main():
    parser = argparse.ArgumentParser(description="Import Name Reference charities")
    parser.add_argument("--excel", type=Path, default=DEFAULT_EXCEL)
    args = parser.parse_args()

    if not args.excel.exists():
        print(f"Excel file not found: {args.excel}")
        sys.exit(1)

    print(f"Importing from: {args.excel}")
    created, skipped, errors = await import_from_excel(args.excel)
    print(f"Done: {created} created, {skipped} skipped, {errors} errors")


if __name__ == "__main__":
    asyncio.run(main())
