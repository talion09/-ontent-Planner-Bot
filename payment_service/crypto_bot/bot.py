from aiocryptopay import AioCryptoPay

from payment_service.config import CRYPTO_BOT_TOKEN, CRYPTO_BOT_NET


class CryptoBot:

    def __init__(self):
        self.aio_crypto_pay = AioCryptoPay(token=CRYPTO_BOT_TOKEN, network=CRYPTO_BOT_NET)

    async def create_invoice(self, accepted_assets: list[str], amount: float):
        return await self.aio_crypto_pay.create_invoice(currency_type="fiat", amount=amount, fiat="RUB",
                                                        accepted_assets=accepted_assets)

    async def get_invoice(self, id: int):
        return await self.aio_crypto_pay.get_invoices(invoice_ids=id)

    async def get_exchange_rates(self):
        return await self.aio_crypto_pay.get_exchange_rates()
