from aiogram.utils.callback_data import CallbackData

calendar_content = CallbackData("calendar_content", "action", "year", "month", "day", "channel_id")

calendar_clb_content = CallbackData("calendar_clb_content", "action", "year", "month", "day", "post_id")

choose_time_content = CallbackData("choose_time_content", "action", "post_id")

hour_clb_content = CallbackData("hour_clb_content", "hour", "post_id")

minute_clb_content = CallbackData("minute_clb_content", "minute", "post_id")




