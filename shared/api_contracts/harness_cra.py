from datetime import date
from typing import Optional

from pydantic import BaseModel


class T3010Financial(BaseModel):
    business_number: str
    fiscal_year_end: date
    revenue_total: Optional[float] = None
    revenue_donations: Optional[float] = None
    revenue_government: Optional[float] = None
    expenses_total: Optional[float] = None
    expenses_programs: Optional[float] = None
    expenses_admin: Optional[float] = None
    expenses_fundraising: Optional[float] = None
    assets_total: Optional[float] = None
    liabilities_total: Optional[float] = None
    num_employees: Optional[int] = None
