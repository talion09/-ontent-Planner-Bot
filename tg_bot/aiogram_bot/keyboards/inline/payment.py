from aiogram.utils.callback_data import CallbackData

payment_clb = CallbackData("payment_clb", "action")

choice_payment = CallbackData("choice_payment", "action", "tariff")

choice_tariff = CallbackData("choice_tariff", "action", "tariff", "price")

choice_plan = CallbackData("choice_plan", "action", "tariff", "price")

choice_currency = CallbackData("choice_currency", "action", "tariff", "price", "asset")

crypto_pay = CallbackData("crypto_pay", "action", "invoice_id", "tariff")