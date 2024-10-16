import aiohttp


class PaymentApi:

    def __init__(self,
                 # session: aiohttp.ClientSession
                 ):
        # self.session = session
        from tg_bot import config
        self.base_url = f"http://{config.api.api_payment}:{config.api.api_payment_port}/"

    async def invoice(self, data=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"{self.base_url}invoice/", json=data) as response:
                return await response.json()

    async def get_invoice(self, id: int):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f"{self.base_url}invoice/{id}") as response:
                return await response.json()

    async def get_exchange_rates(self, params=None):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f"{self.base_url}get_exchange_rates/", params=params) as response:
                return await response.json()

    async def paywave_invoice(self, data=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"{self.base_url}create/", json=data) as response:
                return await response.json()

    async def paywave_check_status(self, data=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"{self.base_url}status/", json=data) as response:
                return await response.json()

    async def rub_uzs(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f"{self.base_url}rub_uzs/") as response:
                return await response.json()
