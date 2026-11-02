import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = "9056359786:AAH0O2g1R5s9f06J9A62D7frYHK3rc6IA1s"
ADMIN_IDS = [742671142, 975190039]
PIN_CODE = "2004"

# Ваша фотография
PHOTO_URL = "https://i.postimg.cc/MKDht3z0/IMG-20261102-WA0031.jpg"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class RSVPState(StatesGroup):
    waiting_for_name = State()

guests_data = {}

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ С радостью приду!", callback_data="rsvp_yes_single")],
        [InlineKeyboardButton(text="🥂 Приду с парой (+1)", callback_data="rsvp_yes_plus1")],
        [InlineKeyboardButton(text="😔 К сожалению, не смогу", callback_data="rsvp_no")],
        [InlineKeyboardButton(text="📍 Frunze Lounge на Яндекс Картах", url="https://yandex.ru/maps/org/frunze_lounge/3435885400?si=nxta9jp4th2tz8pnzrbc3j8a5w")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    caption_text = (
        "✨ *Приглашение на День Рождения* ✨\n\n"
        "Дорогие друзья! В этот особенный вечер я буду безмерно рада "
        "разделить тепло, радость, уютные беседы и отличное настроение с вами! 🤍\n\n"
        "🗓 *Дата:* 23 ноября\n"
        "⏰ *Время:* 19:00\n"
        "📍 *Место:* Frunze Lounge\n"
        "🏢 *Адрес:* Москва, Днепропетровская ул., 2\n"
        "👗 *Дресс-код:* Свободный / Smart Casual\n\n"
        "⚠️ *Пожалуйста, выберите ответ кнопкой ниже до 20 ноября!*"
    )
    try:
        await message.answer_photo(
            photo=PHOTO_URL,
            caption=caption_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logging.error(f"Ошибка отправки фото: {e}")
        await message.answer(caption_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.callback_query(F.data.startswith("rsvp_"))
async def handle_rsvp_choice(call: types.CallbackQuery, state: FSMContext):
    if call.data == "rsvp_yes_single":
        status = "Придёт (1 чел.)"
        count = 1
    elif call.data == "rsvp_yes_plus1":
        status = "Придёт с парой (+1, всего 2 чел.)"
        count = 2
    else:
        status = "Не сможет прийти"
        count = 0

    await state.update_data(status=status, count=count)
    await state.set_state(RSVPState.waiting_for_name)

    await call.message.answer(
        "✍️ Напишите, пожалуйста, в ответном сообщении ваши **Имя и Фамилию**, чтобы мы внесли вас в список гостей:",
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message(RSVPState.waiting_for_name)
async def process_guest_name(message: types.Message, state: FSMContext):
    guest_name = message.text.strip()
    user_data = await state.get_data()
    status = user_data.get("status")
    count = user_data.get("count", 0)

    user = message.from_user
    username_str = f"@{user.username}" if user.username else "без юзернейма"

    guests_data[user.id] = {
        "name": guest_name,
        "username": username_str,
        "status": status,
        "count": count
    }

    await state.clear()

    if count > 0:
        reply_text = f"Спасибо, {guest_name}! Ваш ответ записан. Будем очень ждать вас на празднике! ✨🥂"
    else:
        reply_text = f"Спасибо, {guest_name}, что предупредили! Жаль, что не получится быть вместе в этот вечер 🤍"

    await message.answer(
        f"{reply_text}\n\n"
        f"📍 Frunze Lounge, 23 ноября в 19:00\n"
        f"_(Если планы изменятся, вы можете снова отправить /start)_"
    )

    admin_notification = (
        f"📩 *Новый ответ на приглашение!*\n\n"
        f"👤 *Гость:* {guest_name} ({username_str})\n"
        f"📋 *Статус:* {status}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_notification, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    is_admin = message.from_user.id in ADMIN_IDS
    if not is_admin:
        args = message.text.split()
        if len(args) < 2 or args[1] != PIN_CODE:
            await message.answer("🔒 Введите команду с пин-кодом: `/admin 2004`", parse_mode="Markdown")
            return

    total_attending = sum(g["count"] for g in guests_data.values())
    total_declined = sum(1 for g in guests_data.values() if "Не сможет" in g["status"])

    lines = [
        "📊 *Список ответов гостей:*\n",
        f"✅ Будут: *{total_attending} чел.*",
        f"❌ Не смогут: *{total_declined} чел.*\n",
        "👥 *Детализация:*"
    ]

    if not guests_data:
        lines.append("Пока никто не ответил.")
    else:
        for idx, g in enumerate(guests_data.values(), 1):
            lines.append(f"{idx}. {g['name']} ({g['username']}) — *{g['status']}*")

    await message.answer("\n".join(lines), parse_mode="Markdown")

@dp.message(Command("reset"))
async def cmd_reset(message: types.Message):
    is_admin = message.from_user.id in ADMIN_IDS
    args = message.text.split()
    
    if not is_admin or len(args) < 2 or args[1] != PIN_CODE:
        await message.answer("🔒 Для сброса списка введите: `/reset 2004`", parse_mode="Markdown")
        return

    guests_data.clear()
    await message.answer("🗑 *Список гостей успешно очищен!* Теперь сбор ответов начинается с нуля.", parse_mode="Markdown")

async def health_check(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
