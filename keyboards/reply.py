from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import INITIAL_ADMINS

def get_main_keyboard(is_admin_user: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="⭐ Stars ishlash")],
        [KeyboardButton(text="⭐ Stars yechish"), KeyboardButton(text="👤 Hisobim")],
        [KeyboardButton(text="📋 So'rovlarim"), KeyboardButton(text="📖 Qo'llanma")],
    ]
    if is_admin_user:
        buttons.append([KeyboardButton(text="⚙️ Admin Panel")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="👥 Foydalanuvchilar")],
            [KeyboardButton(text="📥 So'rovlar"), KeyboardButton(text="👑 Adminlar")],
            [KeyboardButton(text="💰 Referal narxi"), KeyboardButton(text="📢 Kanallar")],
            [KeyboardButton(text="✉️ Xabar yuborish"), KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True
    )
