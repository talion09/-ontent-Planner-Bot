from aiogram.utils.callback_data import CallbackData

further = CallbackData("further", "channel_id", "post_id")

sending_clbk = CallbackData("sending_clbk", "action", "channel_id", "post_id")

calendar_clbk = CallbackData("calendar_clbk", "action", "year", "month", "day", "post_id")

choose_time = CallbackData("choose_time", "action", "post_id")

hour_clbk = CallbackData("hour_clbk", "hour", "post_id")

minute_clbk = CallbackData("minute_clbk", "minute", "post_id")

choose_seconds = CallbackData("choose_seconds", "seconds", "channel_id", "post_id")


