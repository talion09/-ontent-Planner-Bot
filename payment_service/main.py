# -*- coding: utf-8 -*-
import asyncio
import logging

from fastapi import FastAPI

from payment_service.coin_market.api import CoinMarket
from payment_service.crypto_bot.bot import CryptoBot
from payment_service.crypto_bot.schema import Invoice
from payment_service.paywave.api import Paywave
from payment_service.paywave.schema import PaywaveInvoice, PaywaveStatus

app = FastAPI(
    title="PaymentService"
)

# CRYPTOBOT
crypto_bot = CryptoBot()


@app.post("/invoice/")
async def create_invoice(invoice: Invoice):
    try:
        data = await crypto_bot.create_invoice(accepted_assets=invoice.accepted_assets, amount=invoice.amount)
        response = {
            "status": "success",
            "data": data,
            "details": None
        }
    except Exception as e:
        response = {
            "status": "error",
            "data": None,
            "details": str(e)
        }
    return response


@app.get("/invoice/{id}/")
async def get_invoice(id: int):
    try:
        data = await crypto_bot.get_invoice(id=id)
        response = {
            "status": "success",
            "data": data,
            "details": None
        }
    except Exception as e:
        response = {
            "status": "error",
            "data": None,
            "details": str(e)
        }
    return response


@app.get("/get_exchange_rates/")
async def get_exchange_rates():
    try:
        data = await crypto_bot.get_exchange_rates()
        filtered_data = [item for item in data if
                         item.source in ["USDT", "BTC", "LTC", "TON"] and item.target == "RUB"]
        response = {
            "status": "success",
            "data": filtered_data,
            "details": None
        }
    except Exception as e:
        response = {
            "status": "error",
            "data": None,
            "details": str(e)
        }
    return response


# PAYWAVE
paywave = Paywave()


@app.post("/create/")
async def create_invoice(payload: PaywaveInvoice):
    try:
        data = await paywave.post(url=paywave.create_invoice_url, data=payload.model_dump(exclude_unset=True))
        response = {
            "status": "success",
            "data": data['data'],
            "details": None
        }
    except Exception as e:
        response = {
            "status": "error",
            "data": None,
            "details": str(e)
        }
    return response


@app.post("/status/")
async def check_status(payload: PaywaveStatus):
    try:
        data = await paywave.post(url=paywave.check_status_url, data=payload.model_dump(exclude_unset=True))
        response = {
            "status": "success",
            "data": data['data'],
            "details": None
        }
    except Exception as e:
        response = {
            "status": "error",
            "data": None,
            "details": str(e)
        }
    return response


# COIN_MARKET
coin_market = CoinMarket(symbol="RUB")
rub_uzs_value = 0


@app.get("/rub_uzs/")
async def rub_uzs():
    try:
        response = {
            "status": "success",
            "data": int(rub_uzs_value),
            "details": None
        }
    except Exception as e:
        response = {
            "status": "error",
            "data": None,
            "details": str(e)
        }
    return response


async def coin_market_func():
    global rub_uzs_value
    while True:
        try:
            rub_uzs_value = await coin_market.get_in_crypto("UZS")
        except Exception as e:
            logging.error(e)
        await asyncio.sleep(600)


asyncio.create_task(coin_market_func())
