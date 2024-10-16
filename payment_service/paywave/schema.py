from pydantic import BaseModel


class PaywaveInvoice(BaseModel):
    currency: str
    paysystem: str
    oper_id: str
    amount: str
    note: str
    sign: str

class PaywaveStatus(BaseModel):
    optoken:str