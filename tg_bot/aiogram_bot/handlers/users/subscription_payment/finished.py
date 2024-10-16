import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tg_bot import user_channel_settings_api, user_channel_api
from tg_bot.aiogram_bot.keyboards.inline.subscription_payment.inline_button import subscription_payment_clb
from tg_bot.aiogram_bot.network.dto.response import Response
from tg_bot.aiogram_bot.network.dto.user_channel import UserChannelSchema
from tg_bot.aiogram_bot.utils.constants import Support


async def subscription_finished(state: FSMContext, p: str):
    data = await state.get_data()
    channel_ids = []

    if 'channel_ids' in data:
        channel_ids = data['channel_ids']

    call = types.CallbackQuery.get_current()
    markup = InlineKeyboardMarkup(row_width=1)

    if p == "dis":
        text = f'''
<b>🚨 Ваша Подписка Закончилась!</b>\n
Мы заметили, что ваша бесплатная пробная подписка на Harvestly истекла. Надеемся, вам понравилось использовать наши эксклюзивные функции!\n\nВы можете легко продлить свою подписку и продолжить наслаждаться всеми преимуществами!\n\n✅  Продолжайте использовать все наши премиальные функции.\n
✅ Получайте постоянные обновления и улучшения.\n\n✅ Поддерживайте нашу команду, чтобы мы могли продолжать создавать полезный контент.\n\nМы ценим каждого пользователя и надеемся, что вы останетесь с нами. Если у вас есть вопросы или пожелания, мы всегда готовы помочь!\n\nДля обратной связи: {Support}\n\n🎁 В знак благодарности за вашу поддержку, мы предлагаем специальную скидку на первый месяц подписки!
        '''

        discount_button = InlineKeyboardButton(
            text="🎁 Скидка на подписку 50%",
            callback_data=subscription_payment_clb.new(
                a="c",
                p=p,
                t="p"
            )
        )
        markup.add(discount_button)

    elif p == "n_dis":
        text = f'''
<b>🚨 Ваша Подписка Закончилась!</b>\n
Не беспокойтесь, вы можете легко продлить свою подписку и продолжить наслаждаться всеми преимуществами!\n\n✅  Продолжайте использовать все наши премиальные функции.\n
✅ Получайте постоянные обновления и улучшения.\n\n✅ Поддерживайте нашу команду, чтобы мы могли продолжать создавать полезный контент.\n\nМы ценим каждого пользователя и надеемся, что вы останетесь с нами. Если у вас есть вопросы или пожелания, мы всегда готовы помочь!\n\nДля обратной связи: {Support}
        '''

        payment_button = InlineKeyboardButton(
            text="Оплатить подписку 💰",
            callback_data=subscription_payment_clb.new(
                a="c",
                p=p,
                t="p"
            )
        )
        markup.add(payment_button)

    back_button = InlineKeyboardButton(
        text="⬅️ Перейти на бесплатную версию",
        callback_data=subscription_payment_clb.new(
            a="c",
            p=p,
            t="f"
        )
    )

    markup.add(back_button)

    if len(channel_ids) > 0:
        success = Response[bool].model_validate(await user_channel_settings_api.update_subscription_id_by_channel_ids(
            data={
                "channel_ids": channel_ids,
                "new_subscription_id": None,
                'created': None,
                'finished': None
            }
        ))
        if not success:
            return

        user_channel_response: Response[list[UserChannelSchema]] = Response[list[UserChannelSchema]].model_validate(
            await user_channel_api.find_by_channels_id(data={"ids": channel_ids})
        )
        for user_channel in user_channel_response.data:
            try:
                await call.bot.send_message(user_channel.user_id, text, reply_markup=markup)
            except Exception as e:
                logging.error(f"subscription_finished {e}")

    else:
        await call.bot.edit_message_text(
            text=text,
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
