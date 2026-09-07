import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Временная база данных в памяти
users_db = {}

def get_balance(user_id: int) -> float:
    return users_db.get(user_id, 0.0)

def add_balance(user_id: int, amount: float) -> float:
    current = get_balance(user_id)
    users_db[user_id] = current + amount
    return users_db[user_id]

# --- Клавиатуры ---

def get_main_inline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Реквизиты", callback_data="btn_requisites")
    builder.button(text="Подача заявки", callback_data="btn_apply")
    builder.button(text="Баланс и вывод", callback_data="btn_balance")
    builder.button(text="Управление каналами", callback_data="btn_channels")
    builder.button(text="Написать в поддержку", callback_data="btn_support")
    builder.button(text="Активные заявки", callback_data="btn_active_requests")
    builder.button(text="Правила и материалы", callback_data="btn_rules")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def get_balance_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Вывод", callback_data="btn_withdraw")
    builder.button(text="Сменить валюту на RUB", callback_data="btn_change_currency")
    builder.button(text="Назад", callback_data="btn_back")
    # Располагаем каждую кнопку с новой строки
    builder.adjust(1)
    return builder.as_markup()

# --- Команды ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name
    text = f"{user_name}, вы в меню участника ClipHub.\nЧто вы хотите сделать?"
    await message.answer(text, reply_markup=get_main_inline_keyboard())

@dp.message(Command("money"))
async def cmd_money(message: types.Message, command: CommandObject):
    if command.args is None:
        await message.answer("⚠️ Ошибка: введите команду в формате `/money <количество>`", parse_mode="Markdown")
        return
    
    try:
        amount = float(command.args.replace(',', '.'))
        new_balance = add_balance(message.from_user.id, amount)
        
        # Убираем дробную часть, если она равна нулю (.0)
        display_balance = int(new_balance) if new_balance.is_integer() else new_balance
        await message.answer(f"✅ Баланс успешно пополнен на **{amount}** USDT.\nТекущий баланс: **{display_balance}** USDT.", parse_mode="Markdown")
    except ValueError:
        await message.answer("⚠️ Ошибка: количество должно быть числом (например, `/money 15.5`)", parse_mode="Markdown")

@dp.message(Command("zero"))
async def cmd_zero(message: types.Message):
    user_id = message.from_user.id
    users_db[user_id] = 0.0
    await message.answer("✅ Ваш баланс успешно обнулен.")

# --- Обработчики кнопок ---

@dp.callback_query(F.data == "btn_balance")
async def process_balance(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    balance = get_balance(user_id)
    
    # Отображаем 0 вместо 0.0 для красоты
    display_balance = int(balance) if balance.is_integer() else balance
    
    text = (
        f"Ваш баланс: {display_balance} USDT.\n\n"
        "Минимальная сумма вывода: 12.0 USDT.\n"
        "Максимальная сумма вывода: — USDT.\n\n"
        "‼️ После одобрения клипов средства начисляются на баланс канала.\n"
        "Чтобы вывести, переведите их на баланс для вывода через меню управления каналами."
    )
    
    await callback.message.edit_text(text, reply_markup=get_balance_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "btn_back")
async def process_back(callback: types.CallbackQuery):
    user_name = callback.from_user.first_name
    text = f"{user_name}, вы в меню участника ClipHub.\nЧто вы хотите сделать?"
    
    await callback.message.edit_text(text, reply_markup=get_main_inline_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "btn_withdraw")
async def process_withdraw(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    balance = get_balance(user_id)
    
    if balance < 12.0:
        await callback.answer("Недостаточно средств. Минимум 12.0 USDT.", show_alert=True)
    else:
        await callback.answer("Запрос на вывод создан (в разработке)", show_alert=True)

@dp.callback_query(F.data == "btn_change_currency")
async def process_change_currency(callback: types.CallbackQuery):
    await callback.answer("Функция смены валюты в разработке", show_alert=True)

# Заглушки для остальных кнопок главного меню
@dp.callback_query(F.data == "btn_requisites")
@dp.callback_query(F.data == "btn_apply")
@dp.callback_query(F.data == "btn_channels")
@dp.callback_query(F.data == "btn_support")
@dp.callback_query(F.data == "btn_active_requests")
@dp.callback_query(F.data == "btn_rules")
async def process_placeholders(callback: types.CallbackQuery):
    await callback.answer("Этот раздел в разработке", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
