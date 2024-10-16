from typing import Optional

from pydantic import BaseModel


class Invoice(BaseModel):
    # currency_type: Optional[str] = None
    # asset: Optional[str] = None
    accepted_assets: list[str]
    amount: float
    # fiat: Optional[str] = None
