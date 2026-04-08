from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ScrapedCharityData(BaseModel):
    business_number: str
    website_url: Optional[str] = None
    annual_report_url: Optional[str] = None
    financial_statements_url: Optional[str] = None
    last_scraped_at: Optional[datetime] = None
    has_new_financial_statements: bool = False
