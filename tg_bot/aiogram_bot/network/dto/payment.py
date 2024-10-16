from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InvoiceSchema(BaseModel):
    invoice_id: int
    status: str
    hash: str
    asset: Optional[str] = None
    amount: float
    bot_invoice_url: str
    description: Optional[str] = None
    created_at: datetime
    allow_comments: bool
    allow_anonymous: bool
    expiration_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    paid_anonymously: Optional[bool] = None
    comment: Optional[str] = None
    hidden_message: Optional[str] = None
    payload: Optional[str] = None
    paid_btn_name: Optional[str] = None
    paid_btn_url: Optional[str] = None
    currency_type: str
    fiat: Optional[str] = None
    paid_asset: Optional[str] = None
    paid_amount: Optional[float] = None
    paid_usd_rate: Optional[float] = None
    fee_asset: Optional[str] = None
    fee_amount: Optional[float] = None
    accepted_assets: Optional[list[str]] = None


class ExchangeRateSchema(BaseModel):
    is_valid: bool
    source: str
    target: str
    rate: float


class PaywaveInvoiceSchema(BaseModel):
    id: int
    optoken: str
    url: str


class PaywaveInvoiceStatusSchema(BaseModel):
    status: str


