import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import firebase_admin
from firebase_admin import credentials, db

# --- КОНФИГ ---
API_TOKEN = '7090442987:AAG8QXmOXKkFjRsKaW56AaYPF_8y_KBXoFY'
ADMIN_ID = 5794963686
STICKER_ID = 'CAACAgIAAxkBAAEQUyRpdf3c_qOfnKoH_rbqP4ytUkiDiAACQhAAAjPFKUmQDtQRpypKgjgE' 
FIREBASE_URL = 'https://roxera-bot-b8465-default-rtdb.europe-west1.firebasedatabase.app/' # Ссылка из консоли Firebase

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    waiting_for_email = State()
    waiting_for_message = State()

def main_kb():
    kb = [
        [types.KeyboardButton(text="Связь"), types.KeyboardButton(text="Визитка")],
        [types.KeyboardButton(text="Контакты"), types.KeyboardButton(text="Другие ссылки")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer_sticker(STICKER_ID)
    await message.answer(f"Здравствуйте, {message.from_user.first_name}! Выберите один из пунктов ниже:", reply_markup=main_kb())

# Инфо-кнопки
@dp.message(F.text == "Визитка")
async def vizitka(message: types.Message):
    await message.answer("Открыть мини-приложение: https://roxera.xyz")

@dp.message(F.text == "Контакты")
async def contacts(message: types.Message):
    await message.answer("Контакты:\nTelegram: @roxera\nEmail: m@roxera.xyz\nБот: @roxera_bot")

@dp.message(F.text == "Другие ссылки")
async def other_links(message: types.Message):
    text = ("Другие ссылки:\nВизитка: https://roxera.xyz\n"
            "Getgems: https://getgems.io/connect-ton\n"
            "Дуб.Аккаунт: @c0nnect_ton\n"
            "TON: connect-ton.ton (or) 3-3-333-3-3.ton")
    await message.answer(text)

# Логика СВЯЗИ
@dp.message(F.text == "Связь")
async def contact_start(message: types.Message, state: FSMContext):
    user_data = db.reference(f'users/{message.from_user.id}').get()
    
    if user_data and 'email' in user_data:
        await message.answer("Пожалуйста, напишите ваше обращение ниже:")
        await state.set_state(Form.waiting_for_message)
    else:
        kb = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="Да"), types.KeyboardButton(text="Нет")]], resize_keyboard=True)
        await message.answer("Так как в процессе ответа могут возникнуть проблемы, желаете ли вы указать почту?", reply_markup=kb)
        await state.set_state(Form.waiting_for_email)

@dp.message(Form.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    if message.text == "Да":
        await message.answer("Введите ваш Email:")
        return
    if message.text != "Нет":
        db.reference(f'users/{message.from_user.id}').update({'email': message.text})
        await message.answer("Почта сохранена!")
    
    await message.answer("Пожалуйста, напишите ваше обращение ниже:", reply_markup=main_kb())
    await state.set_state(Form.waiting_for_message)

@dp.message(Form.waiting_for_message)
async def send_to_admin(message: types.Message, state: FSMContext):
    # Сохраняем в историю
    db.reference(f'history/{message.from_user.id}').push({'text': message.text})
    # Шлем админу
    await bot.send_message(ADMIN_ID, f"ID: {message.from_user.id}\nЮзер: @{message.from_user.username}\n\n{message.text}")
    await message.answer("Сообщение отправлено! Ожидайте ответа.")
    await state.clear()

# Ответ админа (реплаем)
@dp.message(F.from_user.id == ADMIN_ID, F.reply_to_message)
async def admin_ans(message: types.Message):
    try:
        user_id = int(message.reply_to_message.text.split("ID: ")[1].split("\n")[0])
        await bot.send_message(user_id, f"Ответ от владельца:\n\n{message.text}")
        await message.answer("✅ Отправлено")
    except:
        await message.answer("❌ Ошибка: не найден ID")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())