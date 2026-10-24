import urllib.parse
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_share_keyboard(bot_username: str, user_id: int, ref_bonus: str) -> InlineKeyboardMarkup:
    ref_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    share_text = f"🌟 Pro Stars Bot orqali bepul Telegram Stars ishlang!\nHar bir do'stingiz uchun {ref_bonus} ⭐ oling!\n\n👇 Boshlash uchun bosing:"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote(share_text)}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📨 Ulashish ↗", url=share_url)
            ]
        ]
    )

def get_withdraw_presets_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="15 ⭐", callback_data="withdraw:15"),
                InlineKeyboardButton(text="25 ⭐", callback_data="withdraw:25")
            ],
            [
                InlineKeyboardButton(text="50 ⭐", callback_data="withdraw:50"),
                InlineKeyboardButton(text="100 ⭐", callback_data="withdraw:100")
            ],
            [
                InlineKeyboardButton(text="200 ⭐", callback_data="withdraw:200")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="withdraw:cancel")
            ]
        ]
    )

def get_order_admin_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ To'landi (Tasdiqlash)", callback_data=f"order:approve:{order_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"order:reject:{order_id}")
            ]
        ]
    )

def get_sub_channels_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        buttons.append([
            InlineKeyboardButton(text=f"📢 {ch.get('channel_title') or ch.get('channel_id')}", url=ch.get('invite_link') or f"https://t.me/{ch.get('channel_id').replace('@', '')}")
        ])
    buttons.append([
        InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_channels_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        ch_id = ch['channel_id']
        title = ch.get('channel_title') or ch_id
        buttons.append([
            InlineKeyboardButton(text=f"📢 {title}", callback_data="noop"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delchan:{ch_id}")
        ])
    buttons.append([
        InlineKeyboardButton(text="➕ Yangi kanal qo'shish", callback_data="add_channel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
