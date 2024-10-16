import asyncio
import calendar
from datetime import datetime, timedelta, timezone
from typing import List

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.callback_data import CallbackData
from babel.dates import format_date
from dateutil.relativedelta import relativedelta

#
# from tg_bot.aiogram_bot.handlers.users.parsing import media_group_handler
#
#
# class IsMediaGroup(BoundFilter):
#     async def check(self, message: Message):
#         if message.media_group_id is not None:
#             return True
#         else:
#             return False
#
#
API_TOKEN = '6744186681:AAGbO7d30VXQXaWr0bowCZiXc6K4UHQmWok'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


#
# @media_group_handler
# async def send_welcome(messages: List[types.Message]):
#     photo_url1 = 'https://icdn.lenta.ru/images/2022/07/14/13/20220714133344327/wide_16_9_783762cba60ab5eacf1b1b9d57e70a52.jpg'
#     photo_url2 = 'https://habrastorage.org/r/w780/files/c5f/ecf/619/c5fecf619e034ba8935513d6f131a5c4.jpg'
#
#     media = types.MediaGroup()
#     new_caption = "Новое описание для всех элементов медиагруппы"
#
#     print(messages)
#     for message in messages:
#         print(message)
#         if message['photo']:
#             media.attach_photo(message.photo[-1].file_id, caption=new_caption)
#         elif message['video']:
#             media.attach_video(message.video.file_id, caption=new_caption)
#
#     await bot.send_media_group(chat_id=messages[0].chat.id, media=media)

# media_group = [
#     types.InputMediaPhoto(photo_url1),
#     types.InputMediaPhoto(photo_url2),
#     # types.InputMediaDocument(types.InputFile('C:/Users/User/Downloads/Telegram Desktop/timbercraft.uz.txt'))
# ]
#
# markup = InlineKeyboardMarkup(row_width=1)
#
# markup.add(
#     InlineKeyboardButton(text='◀️ Предыдущий',
#                          callback_data=calendar_content.new(action="previous"))
# )
#
# message1 = await message.bot.send_media_group(
#     chat_id=message.from_user.id,
#     media=media_group
# )

# message1 = await message.bot.send_photo(
#     chat_id=message.from_user.id,
#     photo=photo_url1,
#     reply_markup=markup
# )

# message1 = await message.bot.send_video(
#     chat_id=message.from_user.id,
#     video=types.InputFile("C:/Users/User/Downloads/Telegram Desktop/577b77.mp4", filename="577b77.mp4")
# )

# message1 = await message.bot.send_message(
#     chat_id=message.from_user.id,
#     text = "HELLO"
# )

# message1 = await bot.send_document(message.chat.id,types.InputFile("C:/Users/User/Downloads/Telegram Desktop/577b77.mp4", filename="577b77.mp4"))
# await bot.edit_message_media(
#     media=types.InputMediaAnimation("CgACAgIAAxkBAAIppmX0bJUWViqPuv9RWO2KeFgjU5lMAAIGSgACMiSgS6pOnCWl6yWkNAQ"),
#     chat_id=message.from_user.id,
#     message_id=message1.message_id,
#     reply_markup=markup
# )

# Отправляем медиагруппу
# await bot.send_media_group(message.chat.id, media=media_group)
# await asyncio.sleep(2)
# await bot.edit_message_caption(message.from_user.id,message1[0].message_id,caption="123213")
# await bot.send_document(message.chat.id,types.InputFile("C:/Users/User/Downloads/Telegram Desktop/577b77.mp4", filename="577b77.mp4"))


# @dp.message_handler(commands=['edit_caption'])
# async def edit_caption(message: types.Message):
#     # ID чата и ID сообщения, подпись которого нужно изменить
#     chat_id = message.chat.id
#     message_id = ID_сообщения_которое_нужно_изменить
#
#     # Новая подпись
#     new_caption = "Новая подпись для первого изображения в медиагруппе"
#
#     # Попытка изменения подписи
#     try:
#         await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=new_caption)
#         await message.reply("Подпись успешно изменена.")
#     except Exception as e:
#         await message.reply(f"Произошла ошибка: {e}")


def create_calendar(year, month, selected_day=None, language='ru'):
    inline_kb = InlineKeyboardMarkup(row_width=7)

    date = datetime(year, month, 1)
    month_name = format_date(date, 'LLLL YYYY', locale=language)
    # Header with month and year
    inline_kb.row(
        InlineKeyboardButton("Предыдущий", callback_data=f"prev-month_{year}_{month}_{language}"),
        InlineKeyboardButton(month_name, callback_data="current-month"),
        InlineKeyboardButton("Следующий", callback_data=f"next-month_{year}_{month}_{language}")
    )

    # Days of the week
    days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"] if language == 'en' else ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб",
                                                                                "Вс"] if language == 'ru' else ["Дш",
                                                                                                                "Сш",
                                                                                                                "Чш",
                                                                                                                "Пш",
                                                                                                                "Жм",
                                                                                                                "Шн",
                                                                                                                "Як"]
    inline_kb.row(*[InlineKeyboardButton(day, callback_data="none") for day in days])

    # Days in month
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="none"))
            else:
                text = f"✅ {day}" if day == selected_day else str(day)
                row.append(InlineKeyboardButton(text, callback_data=f"day_{year}_{month}_{day}"))
        inline_kb.row(*row)

    # Back button
    inline_kb.row(InlineKeyboardButton("Назад", callback_data="back"))
    return inline_kb


@dp.callback_query_handler(lambda c: c.data.startswith('day_'))
async def handle_day_callback(query: types.CallbackQuery):
    _, year, month, day = query.data.split('_')
    year, month, day = int(year), int(month), int(day)
    await query.message.edit_reply_markup(create_calendar(year, month, selected_day=day))


@dp.callback_query_handler(lambda c: c.data.startswith('prev-month_') or c.data.startswith('next-month_'))
async def handle_month_callback(query: types.CallbackQuery):
    _, year, month, language = query.data.split('_')
    year, month = int(year), int(month)

    if 'prev-month' in query.data:
        new_month = (month - 1) % 12 or 12
        year = year - 1 if month == 1 else year
    elif 'next-month' in query.data:
        new_month = (month + 1) % 12 or 12
        year = year + 1 if month == 12 else year

    await query.message.edit_reply_markup(create_calendar(year, new_month, language))


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    now = datetime.utcnow()
    await message.reply("Выберите дату:", reply_markup=create_calendar(now.year, now.month))


async def main():
    await dp.start_polling()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
