from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMINS

def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="⭐ Stars ishlash")],
        [KeyboardButton(text="⭐ Stars yechish"), KeyboardButton(text="👤 Hisobim")],
        [KeyboardButton(text="📋 So'rovlarim"), KeyboardButton(text="📖 Qo'llanma")],
    ]
    if user_id in ADMINS:
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
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📥 So'rovlar")],
            [KeyboardButton(text="💰 Referal narxini sozlash"), KeyboardButton(text="📢 Kanallar")],
            [KeyboardButton(text="✉️ Xabar yuborish"), KeyboardButton(text="👤 User balansi")],
            [KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True
    )
