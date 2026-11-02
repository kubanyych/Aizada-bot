import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = "9056359786:AAH0O2g1R5s9f06J9A62D7frYHK3rc6IA1s"
ADMIN_CHAT_ID = 742671142
PIN_CODE = "2004"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

guests_data = {}

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ С радостью приду!", callback_data="rsvp_yes_single")],
        [InlineKeyboardButton(text="🥂 Приду с парой (+1)", callback_data="rsvp_yes_plus1")],
        [InlineKeyboardButton(text="😔 К сожалению, не смогу", callback_data="rsvp_no")],
        [InlineKeyboardButton(text="📍 Frunze Lounge на Яндекс Картах", url="https://yandex.ru/maps/org/frunze_lounge/3435885400?si=nxta9jp4th2tz8pnzrbc3j8a5w")]
    ])
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "✨ *Приглашение на День Рождения* ✨\n\n"
        "Дорогие друзья! В этот особенный вечер я буду безмерно рада "
        "разделить тепло, радость, уютные беседы и отличное настроение с вами! 🤍\n\n"
        "🗓 *Дата:* 23 ноября\n"
        "⏰ *Время:* 19:00\n"
        "📍 *Место:* Frunze Lounge\n"
        "🏢 *Адрес:* Москва, Днепропетровская ул., 2\n"
        "👗 *Дресс-код:* Свободный / Smart Casual\n\n"
        "⚠️ *Пожалуйста, подтвердите своё участие кнопкой ниже до 20 ноября!*"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.callback_query(F.data.startswith("rsvp_"))
async def handle_rsvp(call: types.CallbackQuery):
    user = call.from_user
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username_str = f"@{user.username}" if user.username else "без юзернейма"

    if call.data == "rsvp_yes_single":
        status_text = "Придёт (1 человек)"
        response_msg = "Ура! Спасибо за ответ, буду очень ждать встречи! ✨🥂"
        guests_data[user.id] = {"name": full_name, "username": username_str, "status": "Придёт", "count": 1}
    elif call.data == "rsvp_yes_plus1":
        status_text = "Придёт с парой (+1, всего 2 чел.)"
        response_msg = "Замечательно! Жду вас обоих! ✨🎉"
        guests_data[user.id] = {"name": full_name, "username": username_str, "status": "Придёт с +1", "count": 2}
    else:
        status_text = "Не сможет прийти"
        response_msg = "Очень жаль, но спасибо, что предупредили! 🤍"
        guests_data[user.id] = {"name": full_name, "username": username_str, "status": "Отказ", "count": 0}

    await call.message.edit_text(
        f"{response_msg}\n\n"
        f"📍 Frunze Lounge, 23 ноября в 19:00\n\n"
        f"_(Если ваши планы изменятся, вы можете снова нажать /start и выбрать другой ответ)_",
        parse_mode="Markdown"
    )

    admin_notification = (
        f"📩 *Новый ответ на приглашение!*\n\n"
        f"👤 *Гость:* {full_name} ({username_str})\n"
        f"📋 *Статус:* {status_text}"
    )
    try:
        await bot.send_message(ADMIN_CHAT_ID, admin_notification, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")

    await call.answer()

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
  
