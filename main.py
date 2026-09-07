import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Состояния FSM ---
class ChannelAddState(StatesGroup):
    waiting_for_link = State()

# --- База данных в памяти ---
users_db = {}

def get_user_data(user_id: int):
    if user_id not in users_db:
        users_db[user_id] = {
            "balance": 0.0,
            "channels": ["YT SHORTS • zuckerberg_br"]
        }
    return users_db[user_id]

# --- Клавиатуры ---

def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Реквизиты", callback_data="btn_requisites")
    builder.button(text="Подача заявки", callback_data="btn_apply")
    builder.button(text="Баланс и вывод", callback_data="btn_balance")
    builder.button(text="Управление каналами", callback_data="btn_channels")
    # Кнопка с прямой ссылкой в поддержку
    builder.button(text="Написать в поддержку", url="https://t.me/lixiauto")
    builder.button(text="Активные заявки", callback_data="btn_active_requests")
    builder.button(text="Правила и материалы", callback_data="btn_rules")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def get_requisites_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="USDT TRC-20 (не Binance)", callback_data="req_usdt")
    builder.button(text="СБП", callback_data="req_sbp")
    builder.button(text="Назад", callback_data="btn_main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_apply_channels_keyboard(user_channels):
    builder = InlineKeyboardBuilder()
    for ch in user_channels:
        builder.button(text=ch, callback_data=f"apply_ch_{ch}")
    builder.button(text="Вернуться в меню", callback_data="btn_main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_apply_category_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Игровой", callback_data="cat_game")
    builder.button(text="смежный", callback_data="cat_adjacent")
    builder.button(text="аниме", callback_data="cat_anime")
    builder.button(text="дорамы", callback_data="cat_dorama")
    builder.button(text="видео от 500к просмотров", callback_data="cat_500k")
    builder.button(text="Назад", callback_data="btn_apply")
    builder.button(text="Вернуться в меню", callback_data="btn_main_menu")
    builder.adjust(2, 2, 1, 2)
    return builder.as_markup()

def get_balance_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Вывод", callback_data="btn_withdraw")
    builder.button(text="Сменить валюту на RUB", callback_data="btn_change_currency")
    builder.button(text="Назад", callback_data="btn_main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_channels_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить канал", callback_data="btn_add_channel")
    builder.button(text="Мои каналы", callback_data="btn_my_channels")
    builder.button(text="Назад", callback_data="btn_main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_my_channels_keyboard(user_channels):
    builder = InlineKeyboardBuilder()
    for ch in user_channels:
        builder.button(text=ch, callback_data=f"info_ch_{ch}")
    builder.button(text="Назад", callback_data="btn_channels")
    builder.adjust(1)
    return builder.as_markup()

def get_rules_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Открыть правила", url="https://telegra.ph/ClipHub-ot-FunPay-bonusy-za-video-03-18")
    builder.button(text="Вернуться в меню", callback_data="btn_main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_back_to_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Вернуться в меню", callback_data="btn_main_menu")
    return builder.as_markup()

def get_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Отмена", callback_data="btn_channels")
    return builder.as_markup()

# --- Стартовая команда и меню ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    get_user_data(message.from_user.id)
    user_name = message.from_user.first_name
    text = f"{user_name}, вы в меню участника ClipHub.\nЧто вы хотите сделать?"
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "btn_main_menu")
async def process_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_name = callback.from_user.first_name
    text = f"{user_name}, вы в меню участника ClipHub.\nЧто вы хотите сделать?"
    await callback.message.edit_text(text, reply_markup=get_main_keyboard())
    await callback.answer()

# --- Баланс (Команды /money и /zero) ---

@dp.message(Command("money"))
async def cmd_money(message: types.Message, command: CommandObject):
    if command.args is None:
        await message.answer("⚠️ Ошибка: введите команду в формате `/money <количество>`", parse_mode="Markdown")
        return
    try:
        amount = float(command.args.replace(',', '.'))
        data = get_user_data(message.from_user.id)
        data["balance"] += amount
        new_balance = data["balance"]
        display_balance = int(new_balance) if new_balance.is_integer() else new_balance
        await message.answer(f"✅ Баланс пополнен на **{amount}** USDT.\nТекущий баланс: **{display_balance}** USDT.", parse_mode="Markdown")
    except ValueError:
        await message.answer("⚠️ Ошибка: введите число (например, `/money 15.5`)", parse_mode="Markdown")

@dp.message(Command("zero"))
async def cmd_zero(message: types.Message):
    data = get_user_data(message.from_user.id)
    data["balance"] = 0.0
    await message.answer("✅ Ваш баланс успешно обнулен.")

# --- 1. Раздел: Реквизиты ---

@dp.callback_query(F.data == "btn_requisites")
async def process_requisites(callback: types.CallbackQuery):
    text = (
        "Реквизиты:\n"
        "Чтобы зарабатывать с ClipHub, добавьте свои платёжные реквизиты.\n"
        "Изменить их или добавить новые вы можете в любой момент."
    )
    await callback.message.edit_text(text, reply_markup=get_requisites_keyboard())
    await callback.answer()

@dp.callback_query(F.data.in_({"req_usdt", "req_sbp"}))
async def process_req_select(callback: types.CallbackQuery):
    await callback.answer("Ввод реквизитов находится в разработке", show_alert=True)

# --- 2. Раздел: Подача заявки ---

@dp.callback_query(F.data == "btn_apply")
async def process_apply(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    text = (
        "Создаем заявку на оплату ролика с баннером FunPay. "
        "Выберите канал, на котором выпущен видеоролик."
    )
    await callback.message.edit_text(text, reply_markup=get_apply_channels_keyboard(data["channels"]))
    await callback.answer()

@dp.callback_query(F.data.startswith("apply_ch_"))
async def process_apply_channel_selected(callback: types.CallbackQuery):
    channel_name = callback.data.replace("apply_ch_", "")
    text = f"{channel_name}:\nВаш ролик об играх — в игровой тематике, или не об играх — в смежной тематике?"
    await callback.message.edit_text(text, reply_markup=get_apply_category_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def process_category_selected(callback: types.CallbackQuery):
    await callback.answer("Категория выбрана!", show_alert=True)

# --- 3. Раздел: Баланс и вывод ---

@dp.callback_query(F.data == "btn_balance")
async def process_balance(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    balance = data["balance"]
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

@dp.callback_query(F.data == "btn_withdraw")
async def process_withdraw(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    if data["balance"] < 12.0:
        await callback.answer("Недостаточно средств. Минимум 12.0 USDT.", show_alert=True)
    else:
        await callback.answer("Запрос на вывод создан", show_alert=True)

@dp.callback_query(F.data == "btn_change_currency")
async def process_change_currency(callback: types.CallbackQuery):
    await callback.answer("Функция смены валюты в разработке", show_alert=True)

# --- 4. Раздел: Управление каналами ---

@dp.callback_query(F.data == "btn_channels")
async def process_channels(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    data = get_user_data(callback.from_user.id)
    channels_count = len(data["channels"])
    
    text = (
        f"Ваши каналы: {channels_count}\n"
        "Хотите добавить канал или увидеть список ваших каналов?"
    )
    await callback.message.edit_text(text, reply_markup=get_channels_menu_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "btn_add_channel")
async def process_add_channel_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ChannelAddState.waiting_for_link)
    text = (
        "Добавить канал:\n"
        "Чтобы создать канал, отправьте в чат ссылку на него.\n"
        "Пример:\n"
        "https://youtube.com/@username\n"
        "https://tiktok.com/@username"
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard())
    await callback.answer()

@dp.message(ChannelAddState.waiting_for_link)
async def process_channel_link_input(message: types.Message, state: FSMContext):
    link = message.text.strip()
    if link.startswith("http://") or link.startswith("https://"):
        data = get_user_data(message.from_user.id)
        data["channels"].append(link)
        await state.clear()
        
        await message.answer(f"✅ Канал успешно добавлен: {link}", reply_markup=get_back_to_menu_keyboard())
    else:
        await message.answer("⚠️ Пожалуйста, отправьте корректную ссылку, начинающуюся с `https://`", parse_mode="Markdown")

@dp.callback_query(F.data == "btn_my_channels")
async def process_my_channels(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    text = "Мои каналы:\n\nВаши каналы, подключенные к ClipHub:"
    await callback.message.edit_text(text, reply_markup=get_my_channels_keyboard(data["channels"]))
    await callback.answer()

@dp.callback_query(F.data.startswith("info_ch_"))
async def process_channel_info(callback: types.CallbackQuery):
    await callback.answer("Информация о канале в разработке", show_alert=True)

# --- 5. Раздел: Активные заявки ---

@dp.callback_query(F.data == "btn_active_requests")
async def process_active_requests(callback: types.CallbackQuery):
    await callback.answer("Ошибка: у вас нет заявок", show_alert=True)

# --- 6. Раздел: Правила и материалы ---

@dp.callback_query(F.data == "btn_rules")
async def process_rules(callback: types.CallbackQuery):
    text = "Правила и материалы ClipHub:"
    await callback.message.edit_text(text, reply_markup=get_rules_keyboard())
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
