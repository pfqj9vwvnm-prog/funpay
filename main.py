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

# --- Конфигурация валют ---
CURRENCY_CONFIG = {
    "USDT": {
        "min_withdraw": "12.0 USDT",
        "min_value": 12.0,
        "max_withdraw": "— USDT",
        "next": "RUB"
    },
    "RUB": {
        "min_withdraw": "1000.0 RUB",
        "min_value": 1000.0,
        "max_withdraw": "— RUB",
        "next": "UZS"
    },
    "UZS": {
        "min_withdraw": "150000.00 UZS",
        "min_value": 150000.0,
        "max_withdraw": "— UZS",
        "next": "USDT"
    }
}

# --- База данных в памяти ---
users_db = {}

def get_user_data(user_id: int):
    if user_id not in users_db:
        users_db[user_id] = {
            "currency": "USDT",
            "uzs_enabled": True,  # По умолчанию UZS включен
            "balances": {
                "USDT": 0.0,
                "RUB": 0.0,
                "UZS": 0.0
            },
            "channels": ["YT SHORTS • zuckerberg_br"]
        }
    return users_db[user_id]

def get_next_currency(current_currency: str, uzs_enabled: bool) -> str:
    if not uzs_enabled:
        return "RUB" if current_currency == "USDT" else "USDT"
    return CURRENCY_CONFIG[current_currency]["next"]

# --- Клавиатуры ---

def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Реквизиты", callback_data="btn_requisites")
    builder.button(text="Подача заявки", callback_data="btn_apply")
    builder.button(text="Баланс и вывод", callback_data="btn_balance")
    builder.button(text="Управление каналами", callback_data="btn_channels")
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

def get_balance_keyboard(current_currency: str, uzs_enabled: bool = True):
    next_curr = get_next_currency(current_currency, uzs_enabled)
    builder = InlineKeyboardBuilder()
    builder.button(text="Вывод", callback_data="btn_withdraw")
    builder.button(text=f"Сменить валюту на {next_curr}", callback_data="btn_change_currency")
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

# --- Команды показа/скрытия UZS (/showuzs и /hideuzs) ---

@dp.message(Command("showuzs"))
async def cmd_showuzs(message: types.Message):
    data = get_user_data(message.from_user.id)
    data["uzs_enabled"] = True
    await message.answer("✅ Валюта UZS включена.")

@dp.message(Command("hideuzs"))
async def cmd_hideuzs(message: types.Message):
    data = get_user_data(message.from_user.id)
    data["uzs_enabled"] = False
    # Если текущая валюта была UZS, переключаем на USDT
    if data["currency"] == "UZS":
        data["currency"] = "USDT"
    await message.answer("✅ Валюта UZS скрыта.")

# --- Команды пополнения и сброса (/usdt, /usd, /rub, /uzs, /zero) ---

async def handle_add_balance(message: types.Message, command: CommandObject, currency: str):
    if command.args is None:
        await message.answer(f"⚠️ Ошибка: введите команду в формате `/{command.command} <количество>`", parse_mode="Markdown")
        return
    try:
        amount = float(command.args.replace(',', '.'))
        data = get_user_data(message.from_user.id)
        data["balances"][currency] += amount
        new_balance = data["balances"][currency]
        display_balance = int(new_balance) if new_balance.is_integer() else new_balance
        await message.answer(f"✅ Баланс пополнен на **{amount}** {currency}.\nТекущий баланс ({currency}): **{display_balance}** {currency}.", parse_mode="Markdown")
    except ValueError:
        await message.answer("⚠️ Ошибка: введите корректное число", parse_mode="Markdown")

@dp.message(Command("usdt", "usd"))
async def cmd_usdt(message: types.Message, command: CommandObject):
    await handle_add_balance(message, command, "USDT")

@dp.message(Command("rub"))
async def cmd_rub(message: types.Message, command: CommandObject):
    await handle_add_balance(message, command, "RUB")

@dp.message(Command("uzs"))
async def cmd_uzs(message: types.Message, command: CommandObject):
    await handle_add_balance(message, command, "UZS")

@dp.message(Command("zero"))
async def cmd_zero(message: types.Message):
    data = get_user_data(message.from_user.id)
    data["balances"]["USDT"] = 0.0
    data["balances"]["RUB"] = 0.0
    data["balances"]["UZS"] = 0.0
    await message.answer("✅ Все ваши балансы успешно обнулены.")

# --- Отрисовка баланса ---

async def render_balance_screen(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    curr = data["currency"]
    balance = data["balances"][curr]
    display_balance = int(balance) if balance.is_integer() else balance
    cfg = CURRENCY_CONFIG[curr]
    
    text = (
        f"Ваш баланс: {display_balance} {curr}.\n\n"
        f"Минимальная сумма вывода: {cfg['min_withdraw']}.\n"
        f"Максимальная сумма вывода: {cfg['max_withdraw']}."
    )
    
    # Текст предупреждения выводится только для USDT
    if curr == "USDT":
        text += (
            "\n\n‼️ После одобрения клипов средства начисляются на баланс канала.\n"
            "Чтобы вывести, переведите их на баланс для вывода через меню управления каналами."
        )
    
    await callback.message.edit_text(text, reply_markup=get_balance_keyboard(curr, data["uzs_enabled"]))

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
    await render_balance_screen(callback)
    await callback.answer()

@dp.callback_query(F.data == "btn_change_currency")
async def process_change_currency(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    current_curr = data["currency"]
    data["currency"] = get_next_currency(current_curr, data["uzs_enabled"])
    await render_balance_screen(callback)
    await callback.answer()

@dp.callback_query(F.data == "btn_withdraw")
async def process_withdraw(callback: types.CallbackQuery):
    data = get_user_data(callback.from_user.id)
    curr = data["currency"]
    balance = data["balances"][curr]
    cfg = CURRENCY_CONFIG[curr]
    
    if balance < cfg["min_value"]:
        await callback.answer(f"Недостаточно средств. Минимум {cfg['min_withdraw']}.", show_alert=True)
    else:
        await callback.answer("Запрос на вывод создан", show_alert=True)

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
