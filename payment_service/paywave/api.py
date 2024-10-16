import aiohttp

from payment_service.config import API_KEY
from payment_service.paywave.schema import PaywaveInvoice


class Paywave:

    def __init__(self):
        self.create_invoice_url = "https://api.1pay.uz/payin/create"
        self.check_status_url = "https://api.1pay.uz/payin/status"
        self.headers = {
            "Authorization": f"Bearer {API_KEY}"  # Замените на ваш действительный API ключ
        }

    async def post(self, url: str, data: dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, data=data) as response:
                return await response.json()
