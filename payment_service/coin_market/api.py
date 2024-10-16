import aiohttp

from payment_service.config import COIN_MARKET_API_KEY


class CoinMarket:

    def __init__(self, symbol):
        self.symbol = symbol
        self.api_key = COIN_MARKET_API_KEY

    async def get_in_crypto(self, convert: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url = "https://pro-api.coinmarketcap.com/v2/tools/price-conversion",
                    params={"amount": 1, "symbol": self.symbol, "convert": convert},
                    headers={
                        'Accepts': 'application/json',
                        "X-CMC_PRO_API_KEY": str(self.api_key)
                    },
                    ssl=False
            ) as response:

                return (await response.json())["data"][0]["quote"][convert]["price"]