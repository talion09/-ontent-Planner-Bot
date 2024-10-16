from aiogram.utils.callback_data import CallbackData

content_clb = CallbackData("content_clb", "action", "channel_id")

cancel_content = CallbackData("cancel_content")

post_callback = CallbackData("post_callback", "action", "post_id")

redaction_clb = CallbackData("redaction_clb", "action", "channel_id", "post_id")

add_descrip_content = CallbackData("add_descrip_content", "action", "post_id")

url_buttons_clb_content = CallbackData("url_buttons_clb_content", "action", "post_id")

custom_media_content = CallbackData("custom_media_content", "action", "post_id")

gpt_clb_content = CallbackData("gpt_clb_content", "action", "post_id")

auto_sign_clb_content = CallbackData("auto_sign_clb_content", "action", "post_id")

choose_prompts_content = CallbackData("choose_prompts_content", "action", "index", "post_id")

further_content_plan = CallbackData("further_content_plan", "channel_id", "post_id")

choose_seconds_content_plan = CallbackData("choose_seconds_content_plan", "seconds", "channel_id", "post_id")

sending_clbk_content_plan = CallbackData("sending_clbk_content_plan", "action", "channel_id", "post_id")
