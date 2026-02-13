import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv
import os

load_dotenv()
# 🔑 Токен бота (получи у BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Создаём объекты бота и диспетчера
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# --------------------------------------------
# 1. Определяем состояния (FSM)
# --------------------------------------------
class ValentineQuiz(StatesGroup):
    start_state = State()   # приветствие
    question_1 = State()    # первый вопрос
    question_2 = State()    # второй вопрос
    question_3 = State()    # третий вопрос
    final_state = State()   # финал

# --------------------------------------------
# 2. Данные квиза
# --------------------------------------------
QUESTIONS = [
    {
        "text": "Где мы познакомились?",
        "options": ["В кафе ☕", "В институте 🎓", "Через друзей 👥", "В парке 🌳"],
        "correct": "В институте 🎓"
    },
    {
        "text": "Какой мой любимый цвет?",
        "options": ["Красный ❤️", "Синий 💙", "Зелёный 💚", "Фиолетовый 💜"],
        "correct": "Синий 💙"
    },
    {
        "text": "Сколько месяцев мы вместе?",
        "options": ["3", "6", "9", "12"],
        "correct": "12"
    }
]

# Финальное сообщение (поздравление)
FINAL_MESSAGE = (
    "🎉 Ты ответила на все вопросы! Значит, ты точно помнишь всё важное ❤️\n\n"
    "С Днём святого Валентина, моя любимая! 💕\n"
    "Ты — самое лучшее, что случилось в моей жизни. "
    "Пусть каждый наш день будет таким же тёплым, как этот праздник.\n\n"
    "Ловлю тебя в объятия! 🤗"
)

# Ссылка на открытку (можно загрузить свою в Telegram и взять file_id)
# Здесь для примера я использую прямую ссылку
POSTCARD_URL = "https://i.imgur.com/YourImage.jpg"  # поменяй на свою картинку

# --------------------------------------------
# 3. Хендлер команды /start
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

# --------------------------------------------
# 4. Обработчики колбэков
# --------------------------------------------
@dp.callback_query(F.data == "cancel_quiz", StateFilter(ValentineQuiz.start_state))
async def cancel_quiz(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Жаль 😔 Но я всё равно тебя поздравляю! ❤️")
    await callback.message.answer_sticker("CAACAgIAAxkBAAEM..." )  # вставь file_id своего стикера
    await state.clear()

@dp.callback_query(F.data == "start_quiz")
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отлично! Тогда первый вопрос:")
    # Задаём первый вопрос
    q_data = QUESTIONS[0]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=opt, callback_data=f"q1_{i}")] 
        for i, opt in enumerate(q_data["options"])
    ])
    await callback.message.answer(q_data["text"], reply_markup=keyboard)
    await state.set_state(ValentineQuiz.question_1)

# --------------------------------------------
# 5. Проверка ответов для каждого вопроса
# --------------------------------------------
@dp.callback_query(StateFilter(ValentineQuiz.question_1), F.data.startswith("q1_"))
async def process_q1(callback: CallbackQuery, state: FSMContext):
    choice_index = int(callback.data.split("_")[1])
    chosen = QUESTIONS[0]["options"][choice_index]
    correct = QUESTIONS[0]["correct"]

    if chosen == correct:
        await callback.message.edit_text("✅ Верно! Ты всё помнишь ❤️")
        # Переходим ко второму вопросу
        q_data = QUESTIONS[1]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"q2_{i}")]
            for i, opt in enumerate(q_data["options"])
        ])
        await callback.message.answer(q_data["text"], reply_markup=keyboard)
        await state.set_state(ValentineQuiz.question_2)
    else:
        await callback.answer("❌ Не угадала, попробуй ещё!", show_alert=False)
        await callback.message.edit_reply_markup()  # убираем старые кнопки (опционально)
        # Показываем тот же вопрос снова
        q_data = QUESTIONS[0]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"q1_{i}")]
            for i, opt in enumerate(q_data["options"])
        ])
        await callback.message.answer("Попробуй ещё раз 👇", reply_markup=keyboard)

# Аналогично для второго вопроса
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
        await callback.answer("❌ Не совсем так, давай ещё раз!")
        q_data = QUESTIONS[1]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"q2_{i}")]
            for i, opt in enumerate(q_data["options"])
        ])
        await callback.message.answer("Попробуй ещё раз 👇", reply_markup=keyboard)

# Третий вопрос и финал
@dp.callback_query(StateFilter(ValentineQuiz.question_3), F.data.startswith("q3_"))
async def process_q3(callback: CallbackQuery, state: FSMContext):
    choice_index = int(callback.data.split("_")[1])
    chosen = QUESTIONS[2]["options"][choice_index]
    correct = QUESTIONS[2]["correct"]

    if chosen == correct:
        await callback.message.edit_text("🎉 Бинго! Ты ответила на всё!")
        await callback.message.answer(FINAL_MESSAGE)
        # Отправляем открытку
        await callback.message.answer_photo(photo=POSTCARD_URL, caption="С Днём святого Валентина! 💐")
        # Можно ещё отправить стикер
        await callback.message.answer_sticker("CAACAgIAAxkBAAEM...")  # вставь file_id
        await state.clear()
    else:
        await callback.answer("❌ Ой, почти! Попробуй другой вариант.")
        q_data = QUESTIONS[2]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"q3_{i}")]
            for i, opt in enumerate(q_data["options"])
        ])
        await callback.message.answer("Попробуй ещё раз 👇", reply_markup=keyboard)

# --------------------------------------------
# 6. Команда для сброса (если что-то пошло не так)
# --------------------------------------------
@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Поздравление отменено. Просто напиши /start, чтобы начать заново.")

# --------------------------------------------
# 7. Запуск бота
# --------------------------------------------
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
