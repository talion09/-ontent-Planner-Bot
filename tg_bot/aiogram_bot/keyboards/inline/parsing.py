from aiogram.utils.callback_data import CallbackData

add_channel_clb = CallbackData("add_channel_clb")

parsers_user_channel = CallbackData("parsers_user_channel", "channel_id", "action")

parser_channels = CallbackData("parser_channels", "id", "channel_id", "action")

parser_channel_delete = CallbackData("parser_channel_delete", "id", "channel_id", "action")

subscription_payment_parsing_type = CallbackData("subscription_payment_parsing_type",
                                                 "a",
                                                 "p",
                                                 "t")

see_parsed_post = CallbackData("see_parsed_post", "channel_for_parsing_association_id")
see_parsed_post_new = CallbackData("see_parsed_post_new", "channel_for_parsing_association_id")
see_parsed_post_by_date = CallbackData("see_parsed_post_by_date", "channel_for_parsing_association_id")
back_to_posts = CallbackData("back_to_posts", "channel_for_parsing_association_id")
back_to_parser_channels = CallbackData('back_to_parser_channels', 'id', 'channel_id')

parsed_post = CallbackData("parsed_post", "action", 'channel_id')
parsed_post_media = CallbackData("parsed_post", "action", 'channel_id', "post_id")
