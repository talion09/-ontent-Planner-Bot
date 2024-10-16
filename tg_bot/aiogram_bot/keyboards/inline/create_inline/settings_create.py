from aiogram.utils.callback_data import CallbackData

settings_channel = CallbackData("settings_channel", "ch_id", "act", "ex")

settings_timezone = CallbackData("settings_timezone", "timezone", "act")

settings_chatgpt = CallbackData("settings_chatgpt", "act", "ch_id")

set_gpt_api_key = CallbackData("set_gpt_api_key", "act")

del_prompt_clb = CallbackData("del_prompt_clb", "ch_id", "act", "index")

change_prompt_clb = CallbackData("change_prompt_clb", "ch_id", "act", "index")

update_settings_chnl = CallbackData("update_settings_chnl", "ch_id", "act", "v")

update_auto_sign_clb = CallbackData("update_auto_sign_clb", "ch_id", "v")

update_auto_send_clb = CallbackData("update_auto_send_clb", "ch_id", "v")

#
snap_gpt4 = CallbackData("snap_gpt4", "channel_id")
snap_gpt4_next = CallbackData("snap_gpt4_next", "channel_id")
untie_gpt_account = CallbackData("untie_gpt_account", "channel_id")
