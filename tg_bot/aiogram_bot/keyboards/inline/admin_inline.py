from aiogram.utils.callback_data import CallbackData

admin_buttons_clb = CallbackData("admin_buttons_clb", "post_id")

admin_cancel_create = CallbackData("admin_cancel_create", "post_id")

admin_further = CallbackData("admin_further", "post_id")

admin_sending_clb = CallbackData("admin_sending_clb", "action", "post_id")

admin_calendar_clb = CallbackData("admin_calendar_clb", "action", "year", "month", "day", "post_id")

admin_choose_time = CallbackData("admin_choose_time", "action", "post_id")

admin_hour_clb = CallbackData("admin_hour_clb", "hour", "post_id")

admin_minute_clb = CallbackData("admin_minute_clb", "minute", "post_id")
