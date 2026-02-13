import asyncio
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --------------------------------------------
# 1. Функция экранирования для MarkdownV2
# --------------------------------------------
def escape_markdownv2(text: str) -> str:
    """Экранирует спецсимволы MarkdownV2: _ * [ ] ( ) ~ ` > # + - = | { } . !"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

# --------------------------------------------
# 2. Анимация "печатающегося текста"
# --------------------------------------------
async def animate_typing(
    bot: Bot,
    chat_id: int,
    text: str,
    parse_mode: str = "MarkdownV2",
    delay: float = 0.15
):
    words = text.split(' ')
    current_text = ""
    sent_message = None

    for i, word in enumerate(words):
        if i == 0:
            current_text = word
        else:
            current_text += " " + word

        if sent_message is None:
            sent_message = await bot.send_message(chat_id, current_text, parse_mode=parse_mode)
        else:
            # 👇 Используем именованные аргументы, чтобы избежать путаницы
            await bot.edit_message_text(
                text=current_text,
                chat_id=chat_id,
                message_id=sent_message.message_id,
                parse_mode=parse_mode
            )

        await asyncio.sleep(delay)

    return sent_message

# --------------------------------------------
# 3. Определяем состояния (FSM)
# --------------------------------------------
class ValentineQuiz(StatesGroup):
    start_state = State()
    question_1 = State()
    question_2 = State()
    question_3 = State()
    question_4 = State()
    final_state = State()

# --------------------------------------------
# 4. Данные квиза
# --------------------------------------------
QUESTIONS = [
    {
        "text": "Где мы познакомились?",
        "options": ["В кафейне ☕", "В универе 🎓", "В парке 🌳"],
        "correct": "В универе 🎓"
    },
    {
        "text": "В какое время года мы начали встречаться?",
        "options": ["🍀", "🌳", "🍂", "❄️"],
        "correct": "❄️"
    },
    {
        "text": "Какой мой любимый цвет?",
        "options": ["❤️", "💙", "💚", "💜"],
        "correct": "💙"
    },
    {
        "text": "Сколько лет мы вместе?",
        "options": ["6️⃣", "7️⃣", "8️⃣"],
        "correct": "7️⃣"
    }
]

# Финальное сообщение (будет экранировано перед отправкой)
FINAL_MESSAGE = (
    "🎉 Ты ответила на все вопросы! Значит, ты точно помнишь всё важное ❤️\n\n"
    "С Днём святого Валентина, любимая! 💕\n"
    "Ты — самое лучшее, что случилось в моей жизни. "
    "Люблю тебя очень сильно!.\n\n"
    "Ловлю тебя в объятия! 🤗"
)

POSTCARD_URL = "https://img.freepik.com/free-photo/valentine-s-day-still-life-decorations_23-2151934456.jpg"  # замени на реальную ссылку или file_id

# --------------------------------------------
# 5. Хендлеры
# --------------------------------------------
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💘 Начать поздравление", callback_data="start_quiz")],
        [InlineKeyboardButton(text="❌ Нет, спасибо", callback_data="cancel_quiz")]
    ])
    await message.answer(
        "Привет, красавица! 👋\n"
        "Я приготовил для тебя необычное поздравление. "
        "Хочешь получить его?",
        reply_markup=keyboard
    )
    await state.set_state(ValentineQuiz.start_state)

@dp.callback_query(F.data == "cancel_quiz", StateFilter(ValentineQuiz.start_state))
async def cancel_quiz(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Жаль 😔 Но я всё равно тебя поздравляю! ❤️")
    # await callback.message.answer_sticker("CAACAgIAAxkBAAEM...")
    await state.clear()

@dp.callback_query(F.data == "start_quiz")
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отлично! Тогда первый вопрос:")
    q_data = QUESTIONS[0]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=opt, callback_data=f"q1_{i}")] 
        for i, opt in enumerate(q_data["options"])
    ])
    await callback.message.answer(q_data["text"], reply_markup=keyboard)
    await state.set_state(ValentineQuiz.question_1)

@dp.callback_query(StateFilter(ValentineQuiz.question_1), F.data.startswith("q1_"))
async def process_q1(callback: CallbackQuery, state: FSMContext):
    choice_index = int(callback.data.split("_")[1])
    chosen = QUESTIONS[0]["options"][choice_index]
    correct = QUESTIONS[0]["correct"]

    if chosen == correct:
        await callback.message.edit_text("✅ Верно! Ты всё помнишь ❤️")
        q_data = QUESTIONS[1]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"q2_{i}")]
            for i, opt in enumerate(q_data["options"])
        ])
        await callback.message.answer(q_data["text"], reply_markup=keyboard)
        await state.set_state(ValentineQuiz.question_2)
    else:
        await callback.answer("❌ Не угадала, попробуй ещё!", show_alert=False)
        q_data = QUESTIONS[0]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"q1_{i}")]
            for i, opt in enumerate(q_data["options"])
        ])
        await callback.message.answer("Попробуй ещё раз 👇", reply_markup=keyboard)

@dp.callback_query(StateFilter(ValentineQuiz.question_2), F.data.startswith("q2_"))
async def process_q2(callback: CallbackQuery, state: FSMContext):
    choice_index = int(callback.data.split("_")[1])
    chosen = QUESTIONS[1]["options"][choice_index]
    correct = QUESTIONS[1]["correct"]

    if chosen == correct:
        await callback.message.edit_text("✅ Супер! Идём дальше ✨")
        q_data = QUESTIONS[2]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"q3_{i}")]
            for i, opt in enumerate(q_data["options"])
        ])
        await callback.message.answer(q_data["text"], reply_markup=keyboard)
        await state.set_state(ValentineQuiz.question_3)
    else:
        await callback.answer("❌ Не совсем так, давай ещё раз")
        q_data = QUESTIONS[1]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"q2_{i}")]
            for i, opt in enumerate(q_data["options"])
        ])
        await callback.message.answer("Попробуй ещё раз 👇", reply_markup=keyboard)

@dp.callback_query(StateFilter(ValentineQuiz.question_3), F.data.startswith("q3_"))
async def process_q3(callback: CallbackQuery, state: FSMContext):
    choice_index = int(callback.data.split("_")[1])
    chosen = QUESTIONS[2]["options"][choice_index]
    correct = QUESTIONS[2]["correct"]

    if chosen == correct:
        await callback.message.edit_text("✅ Супер! Идём дальше ✨")
        q_data = QUESTIONS[3]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"q4_{i}")]
            for i, opt in enumerate(q_data["options"])
        ])
        await callback.message.answer(q_data["text"], reply_markup=keyboard)
        await state.set_state(ValentineQuiz.question_4)
    else:
        await callback.answer("❌ Неа, попробуй снова")
        q_data = QUESTIONS[2]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"q3_{i}")]
            for i, opt in enumerate(q_data["options"])
        ])
        await callback.message.answer("Попробуй ещё раз 👇", reply_markup=keyboard)

@dp.callback_query(StateFilter(ValentineQuiz.question_4), F.data.startswith("q4_"))
async def process_q4(callback: CallbackQuery, state: FSMContext):
    choice_index = int(callback.data.split("_")[1])
    chosen = QUESTIONS[3]["options"][choice_index]
    correct = QUESTIONS[3]["correct"]

    if chosen == correct:
        await callback.message.edit_text("🎉 Бинго! Ты ответила на всё!")

        # Экранируем финальное сообщение
        escaped_final = escape_markdownv2(FINAL_MESSAGE)

        # Анимируем появление текста
        await animate_typing(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text=escaped_final,
            parse_mode="MarkdownV2",
            delay=0.12
        )

        # Отправляем открытку и стикер
        await callback.message.answer_photo(photo=POSTCARD_URL, caption="С Днём святого Валентина! 💐")
        # await callback.message.answer_sticker("CAACAgIAAxkBAAEM...")
        await state.clear()
    else:
        await callback.answer("❌ Ой, почти! Попробуй другой вариант.")
        q_data = QUESTIONS[3]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"q4_{i}")]
            for i, opt in enumerate(q_data["options"])
        ])
        await callback.message.answer("Попробуй ещё раз 👇", reply_markup=keyboard)

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Упс.. Ошибка. Просто напиши /start, чтобы начать заново.")

# --------------------------------------------
# 6. Запуск бота
# --------------------------------------------
async def main():
    print("Бот запущен...")
    # Если нужен прокси:
    session = AiohttpSession(proxy='http://192.168.250.193:3128')
    bot = Bot(token=BOT_TOKEN, session=session)
    # Если прокси не нужен, замени на:
    # bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
