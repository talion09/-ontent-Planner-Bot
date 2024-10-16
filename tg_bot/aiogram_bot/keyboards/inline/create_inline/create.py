from aiogram.utils.callback_data import CallbackData

creating_clb = CallbackData("creating_clb", "channel_id")

add_descrip = CallbackData("add_descrip", "post_id")

url_buttons_clb = CallbackData("url_buttons_clb", "post_id")

custom_media = CallbackData("custom_media", "action", "post_id")

gpt_clb = CallbackData("gpt_clb", "post_id")

auto_sign_clb = CallbackData("auto_sign_clb", "post_id")

cancel_create = CallbackData("cancel_create", "post_id")

replace_media = CallbackData("replace_media", "action", "id_photo", "post_id")

swap_media_clb = CallbackData("swap_media_clb", "action", "id_1", "id_2", "post_id")

choose_prompts = CallbackData("choose_prompts", "action", "index", "post_id")

create_sign = CallbackData("create_sign", "post_id")

create_post_prompt = CallbackData("create_post_prompt", "channel_id", "post_id", "action")

