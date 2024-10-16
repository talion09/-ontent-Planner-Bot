from aiogram.utils.callback_data import CallbackData

# a - action
# p - prefix
# t - type
# t_ch - tapped channel
# m - month

subscription_payment_clb = CallbackData("subscription_payment_clb",
                                        "a",
                                        "p",
                                        "t"
                                        )
subscription_payment_channel_tap_clb = CallbackData("subscription_payment_channel_tap_clb",
                                                    't_ch',
                                                    "p",
                                                    "t",
                                                    )
subscription_payment_month_tap_clb = CallbackData("subscription_payment_month_tap_clb",
                                                  "m",
                                                  "p",
                                                  "t")
subscription_payment_back_clb = CallbackData("subscription_payment_back_clb",
                                             "a",
                                             "p",
                                             "t")

subscription_payment_check_invoice_clb = CallbackData("subscription_payment_check_invoice_clb", "a")

# FREE
subscription_payment_free_clb = CallbackData("subscription_payment_free_clb",
                                             "a",
                                             "p",
                                             "t")

# TRIAL
subscription_payment_trial_clb = CallbackData("subscription_payment_trial_clb",
                                              "a",
                                              "p")
