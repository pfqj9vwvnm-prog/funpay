import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Получение токена из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Функция для генерации клавиатуры
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    
    # Ряд 1
    builder.button(text="Реквизиты")
    builder.button(text="Подача заявки")
    
    # Ряд 2
    builder.button(text="Баланс и вывод")
    builder.button(text="Управление каналами")
    
    # Ряд 3
    builder.button(text="Написать в поддержку")
    builder.button(text="Активные заявки")
    
    # Ряд 4
    builder.button(text="Правила и материалы")
    
    # Настройка сетки: 2, 2, 2, 1
    builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup(resize_keyboard=True)

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name
    text = f"{user_name}, вы в меню участника ClipHub.\nЧто вы хотите сделать?"
    await message.answer(text, reply_markup=get_main_keyboard())

# --- Пустые обработчики кнопок ---

@dp.message(F.text == "Реквизиты")
async def btn_requisites(message: types.Message):
    # Место для вашего кода
    pass

@dp.message(F.text == "Подача заявки")
async def btn_apply(message: types.Message):
    # Место для вашего кода
    pass

@dp.message(F.text == "Баланс и вывод")
async def btn_balance(message: types.Message):
    # Место для вашего кода
    pass

@dp.message(F.text == "Управление каналами")
async def btn_channels(message: types.Message):
    # Место для вашего кода
    pass

@dp.message(F.text == "Написать в поддержку")
async def btn_support(message: types.Message):
    # Место для вашего кода
    pass

@dp.message(F.text == "Активные заявки")
async def btn_active_requests(message: types.Message):
    # Место для вашего кода
    pass

@dp.message(F.text == "Правила и материалы")
async def btn_rules(message: types.Message):
    # Место для вашего кода
    pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
