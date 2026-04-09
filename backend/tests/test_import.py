"""Tests for Phase 9 import scripts (F080-F083).

Uses fixture data (dict records) instead of Excel files.
"""

import sys
from pathlib import Path

import pytest
from sqlalchemy import select

# Add scripts to path for import
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "import"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.charity import Charity
from app.models.financial_analysis import FinancialAnalysis
from app.models.rating import CharityRating
from app.models.profile_content import ProfileContent
from app.models.srss import SRSSScore, SRSSHistorical
from app.models.evaluation import Evaluation
from app.models.priority import PriorityScore
from app.models.user import User


# --- Fixture data ---

NAME_REF_RECORDS = [
    {
        "BN/Registration Number": "119219814RR0001",
        "Formal Name": "Canadian Red Cross Society",
        "Common Name": "Red Cross",
        "Sector": "Social Services",
        "Sub-Sector": "Emergency",
        "Fiscal Year End": "2024-03-31",
        "Website": "https://redcross.ca",
        "City": "Ottawa",
        "Province": "ON",
        "Top 100": True,
        "Total Revenue": 500000000.0,
        "Donations": 300000000.0,
        "Government Funding": 150000000.0,
        "Total Expenses": 480000000.0,
        "Program Costs": 400000000.0,
        "Admin Costs": 50000000.0,
        "Fundraising Costs": 30000000.0,
        "Reserves": 100000000.0,
        "Star Rating": 4,
        "Impact X": 8.5,
        "Impact Y": 7.2,
        "Impact Label": "High Efficiency / High Impact",
        "Results and Impact": "<p>Red Cross delivers humanitarian aid globally.</p>",
        "Mission": "Improve lives of vulnerable people.",
    },
    {
        "BN/Registration Number": "108076480RR0001",
        "Formal Name": "SickKids Foundation",
        "Common Name": "SickKids",
        "Sector": "Health",
        "Fiscal Year End": "2024-06-30",
        "Total Revenue": 200000000.0,
        "Total Expenses": 180000000.0,
        "Program Costs": 150000000.0,
        "Admin Costs": 20000000.0,
        "Fundraising Costs": 10000000.0,
    },
    {
        "Formal Name": "Unknown Charity",
    },
]

JD_CHARITIES_RECORDS = [
    {
        "BN/Registration Number": "119219814RR0001",
        "Formal Name": "Canadian Red Cross Society",
        "Sector": "Social Services",
        "Sector Group": "Human Services",
        "Fiscal Year End": "2024-03-31",
        "Total Revenue": 500000000.0,
        "Total Expenses": 480000000.0,
        "Program Costs": 400000000.0,
        "Admin Costs": 50000000.0,
        "Fundraising Costs": 30000000.0,
        "Q1": 7, "Q2": 6, "Q3": 8, "Q4": 7,
        "Q5": 6, "Q6": 7, "Q7": 5, "Q8": 6,
        "Q9": 7, "Q10": 8, "Q11": 6, "Q12": 7, "Q13": 5,
        "Q14": 6, "Q15": 7, "Q16": 8, "Q17": 6, "Q18": 7,
        "Q19": 7, "Q20": 6, "Q21": 8, "Q22": 7,
        "Q23": 6, "Q24": 7, "Q25": 5, "Q26": 6,
        "Strategy %": 87.5, "Activities %": 75.0,
        "SRSS Total %": 78.0, "SRSS Grade": "B+",
        "Star Rating": 4,
        "Impact X": 8.5, "Impact Y": 7.2,
        "Overhead %": 16.67,
        "Year": 2025,
    },
]

SUMMER_2025_RECORDS = [
    {
        "BN/Registration Number": "119219814RR0001",
        "Formal Name": "Canadian Red Cross Society",
        "Status": "financial analysis",
        "Analyst": "Test Analyst",
        "Notes": "Good progress on financials",
        "Financial Notes": "AFS received from CRA",
        "Priority": 1,
        "Composite Score": 4.5,
    },
]

HISTORICAL_RECORDS = [
    {
        "BN/Registration Number": "119219814RR0001",
        "Formal Name": "Canadian Red Cross Society",
        "Status": "done",
        "SRSS 2020": 72.0,
        "SRSS 2021": 75.0,
        "SRSS 2022": 78.0,
        "Composite Score": 4.2,
        "Priority": 2,
        "Views Score": 4.0,
        "Staleness Score": 3.0,
        "Demand Score": 2.5,
        "Top 100 Bonus": 5.0,
    },
]


# --- F080: Import Name Reference ---

@pytest.mark.asyncio
async def test_import_name_reference_charities(db_session):
    from import_name_reference import import_from_records

    stats = await import_from_records(NAME_REF_RECORDS, db_session)
    assert stats["charities_created"] == 2
    assert stats["charities_skipped"] == 1
    assert stats["errors"] == 0


@pytest.mark.asyncio
async def test_import_name_reference_financials(db_session):
    from import_name_reference import import_from_records

    stats = await import_from_records(NAME_REF_RECORDS, db_session)
    assert stats["financials_created"] == 2

    result = await db_session.execute(select(FinancialAnalysis))
    fas = list(result.scalars().all())
    red_cross_fa = [fa for fa in fas if fa.total_revenue == 500000000.0]
    assert len(red_cross_fa) == 1
    assert red_cross_fa[0].admin_percent is not None
    assert red_cross_fa[0].overhead_percent is not None


@pytest.mark.asyncio
async def test_import_name_reference_ratings(db_session):
    from import_name_reference import import_from_records

    stats = await import_from_records(NAME_REF_RECORDS, db_session)
    assert stats["ratings_created"] >= 1

    result = await db_session.execute(select(CharityRating))
    ratings = list(result.scalars().all())
    assert any(r.star_rating == 4 for r in ratings)


@pytest.mark.asyncio
async def test_import_name_reference_content(db_session):
    from import_name_reference import import_from_records

    stats = await import_from_records(NAME_REF_RECORDS, db_session)
    assert stats["content_created"] >= 2

    result = await db_session.execute(
        select(ProfileContent).where(ProfileContent.section_type == "results_impact")
    )
    content = list(result.scalars().all())
    assert len(content) >= 1


@pytest.mark.asyncio
async def test_import_name_reference_dedup(db_session):
    from import_name_reference import import_from_records

    stats1 = await import_from_records(NAME_REF_RECORDS, db_session)
    stats2 = await import_from_records(NAME_REF_RECORDS, db_session)
    assert stats1["charities_created"] == 2
    assert stats2["charities_created"] == 0
    assert stats2["charities_skipped"] >= 2


# --- F081: Import JD Charities List ---

@pytest.mark.asyncio
async def test_import_jd_charities_srss(db_session):
    from import_name_reference import import_from_records as import_nr
    from import_jd_charities import import_from_records

    await import_nr(NAME_REF_RECORDS[:1], db_session)
    stats = await import_from_records(JD_CHARITIES_RECORDS, db_session)
    assert stats["srss_created"] == 1
    assert stats["errors"] == 0

    result = await db_session.execute(select(SRSSScore))
    scores = list(result.scalars().all())
    assert len(scores) == 1
    assert scores[0].q1 == 7
    assert scores[0].letter_grade == "B+"


@pytest.mark.asyncio
async def test_import_jd_charities_sectors(db_session):
    from import_name_reference import import_from_records as import_nr
    from import_jd_charities import import_from_records

    await import_nr(NAME_REF_RECORDS[:1], db_session)
    stats = await import_from_records(JD_CHARITIES_RECORDS, db_session)
    assert stats["sectors_created"] >= 1


@pytest.mark.asyncio
async def test_import_jd_charities_ratings(db_session):
    from import_name_reference import import_from_records as import_nr
    from import_jd_charities import import_from_records

    await import_nr(NAME_REF_RECORDS[:1], db_session)
    stats = await import_from_records(JD_CHARITIES_RECORDS, db_session)
    assert stats["ratings_created"] == 1


# --- F082: Import Summer 2025 ---

@pytest.mark.asyncio
async def test_import_summer_2025_evaluations(db_session):
    from import_name_reference import import_from_records as import_nr
    from import_summer_2025 import import_from_records

    await import_nr(NAME_REF_RECORDS[:1], db_session)
    stats = await import_from_records(SUMMER_2025_RECORDS, db_session)
    assert stats["evaluations_created"] == 1
    assert stats["errors"] == 0

    result = await db_session.execute(select(Evaluation))
    evals = list(result.scalars().all())
    assert len(evals) == 1
    assert evals[0].stage == "financial_analysis"


@pytest.mark.asyncio
async def test_import_summer_2025_notes(db_session):
    from import_name_reference import import_from_records as import_nr
    from import_summer_2025 import import_from_records
    from app.auth.password import hash_password

    await import_nr(NAME_REF_RECORDS[:1], db_session)

    analyst = User(
        email="test_analyst@test.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test Analyst",
        role="analyst",
    )
    db_session.add(analyst)
    await db_session.flush()

    stats = await import_from_records(SUMMER_2025_RECORDS, db_session, system_user_id=analyst.id)
    assert stats["notes_created"] >= 2


@pytest.mark.asyncio
async def test_import_summer_2025_priorities(db_session):
    from import_name_reference import import_from_records as import_nr
    from import_summer_2025 import import_from_records

    await import_nr(NAME_REF_RECORDS[:1], db_session)
    stats = await import_from_records(SUMMER_2025_RECORDS, db_session)
    assert stats["priorities_created"] == 1

    result = await db_session.execute(select(PriorityScore))
    priorities = list(result.scalars().all())
    assert len(priorities) == 1
    assert priorities[0].priority_rank == 1


@pytest.mark.asyncio
async def test_import_summer_2025_skips_missing(db_session):
    from import_summer_2025 import import_from_records

    stats = await import_from_records(SUMMER_2025_RECORDS, db_session)
    assert stats["skipped"] == 1
    assert stats["evaluations_created"] == 0


# --- F083: Import historical data ---

@pytest.mark.asyncio
async def test_import_historical_srss(db_session):
    from import_name_reference import import_from_records as import_nr
    from import_historical import import_srss_historical

    await import_nr(NAME_REF_RECORDS[:1], db_session)
    stats = await import_srss_historical(HISTORICAL_RECORDS, db_session)
    assert stats["records_created"] == 3
    assert stats["errors"] == 0

    result = await db_session.execute(
        select(SRSSHistorical).order_by(SRSSHistorical.year)
    )
    hist = list(result.scalars().all())
    assert len(hist) == 3
    assert hist[0].year == 2020
    assert hist[0].total_pct == 72.0
    assert hist[0].letter_grade == "B+"


@pytest.mark.asyncio
async def test_import_historical_srss_dedup(db_session):
    from import_name_reference import import_from_records as import_nr
    from import_historical import import_srss_historical

    await import_nr(NAME_REF_RECORDS[:1], db_session)
    stats1 = await import_srss_historical(HISTORICAL_RECORDS, db_session)
    stats2 = await import_srss_historical(HISTORICAL_RECORDS, db_session)
    assert stats1["records_created"] == 3
    assert stats2["records_created"] == 0


@pytest.mark.asyncio
async def test_import_historical_summer_2024(db_session):
    from import_name_reference import import_from_records as import_nr
    from import_historical import import_summer_2024

    await import_nr(NAME_REF_RECORDS[:1], db_session)
    stats = await import_summer_2024(HISTORICAL_RECORDS, db_session)
    assert stats["evaluations_created"] == 1
    assert stats["charities_linked"] == 1

    result = await db_session.execute(select(Evaluation))
    evals = list(result.scalars().all())
    assert len(evals) == 1
    assert evals[0].stage == "published"


@pytest.mark.asyncio
async def test_import_historical_priority(db_session):
    from import_name_reference import import_from_records as import_nr
    from import_historical import import_priority_reference

    await import_nr(NAME_REF_RECORDS[:1], db_session)
    stats = await import_priority_reference(HISTORICAL_RECORDS, db_session)
    assert stats["priorities_created"] == 1
    assert stats["errors"] == 0

    result = await db_session.execute(select(PriorityScore))
    priorities = list(result.scalars().all())
    assert len(priorities) == 1
    assert priorities[0].composite_score == 4.2
    assert priorities[0].views_score == 4.0


@pytest.mark.asyncio
async def test_import_historical_combined(db_session):
    from import_name_reference import import_from_records as import_nr
    from import_historical import import_from_records

    await import_nr(NAME_REF_RECORDS[:1], db_session)
    stats = await import_from_records(HISTORICAL_RECORDS, db_session)
    assert stats["summer_2024"]["evaluations_created"] == 1
    assert stats["srss_historical"]["records_created"] == 3
    assert stats["priority_reference"]["priorities_created"] == 1
