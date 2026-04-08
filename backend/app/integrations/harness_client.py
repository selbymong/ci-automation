import sys
from datetime import date, datetime
from typing import Optional

import httpx

from app.config import settings

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
from shared.api_contracts.harness_cra import T3010Financial
from shared.api_contracts.harness_scrape import ScrapedCharityData


class HarnessClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def get_t3010_data(self, bn: str) -> Optional[T3010Financial]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/cra/t3010/{bn}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return T3010Financial(**resp.json())

    async def get_scraped_data(self, bn: str) -> Optional[ScrapedCharityData]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/scrape/charity/{bn}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return ScrapedCharityData(**resp.json())

    async def get_organization(self, bn: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/organizations/{bn}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()


class MockHarnessClient:
    async def get_t3010_data(self, bn: str) -> T3010Financial:
        return T3010Financial(
            business_number=bn,
            fiscal_year_end=date(2024, 3, 31),
            revenue_total=5_000_000.0,
            revenue_donations=3_000_000.0,
            revenue_government=1_500_000.0,
            expenses_total=4_800_000.0,
            expenses_programs=3_500_000.0,
            expenses_admin=800_000.0,
            expenses_fundraising=500_000.0,
            assets_total=2_000_000.0,
            liabilities_total=500_000.0,
            num_employees=45,
        )

    async def get_scraped_data(self, bn: str) -> ScrapedCharityData:
        return ScrapedCharityData(
            business_number=bn,
            website_url=f"https://example.org/{bn}",
            annual_report_url=f"https://example.org/{bn}/annual-report.pdf",
            financial_statements_url=f"https://example.org/{bn}/financials.pdf",
            last_scraped_at=datetime(2025, 1, 15),
            has_new_financial_statements=True,
        )

    async def get_organization(self, bn: str) -> dict:
        return {
            "business_number": bn,
            "legal_name": f"Test Organization {bn}",
            "status": "registered",
        }


def get_harness_client() -> HarnessClient | MockHarnessClient:
    if settings.HARNESS_API_MOCK:
        return MockHarnessClient()
    return HarnessClient(
        base_url=settings.HARNESS_API_URL,
        api_key=settings.HARNESS_API_KEY,
    )
