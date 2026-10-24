import urllib.parse
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_OWNER_ID

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

# Users Management Inline Keyboards
def get_users_mgmt_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏆 Top 10 Referallar", callback_data="users:top_referrers"),
                InlineKeyboardButton(text="🆕 So'nggi 10 ta user", callback_data="users:recent")
            ],
            [
                InlineKeyboardButton(text="🔍 Foydalanuvchini qidirish", callback_data="users:search")
            ]
        ]
    )

def get_user_actions_keyboard(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    ban_text = "✅ Blokdan chiqarish" if is_banned else "🚫 Bloklash"
    ban_action = "unban" if is_banned else "ban"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Balansni o'zgartirish", callback_data=f"uact:balance:{user_id}"),
                InlineKeyboardButton(text=ban_text, callback_data=f"uact:{ban_action}:{user_id}")
            ],
            [
                InlineKeyboardButton(text="✉️ Shaxsiy xabar yuborish", callback_data=f"uact:dm:{user_id}")
            ]
        ]
    )

# Admins Management Inline Keyboards
def get_admins_mgmt_keyboard(admins: list[dict], current_user_id: int = None) -> InlineKeyboardMarkup:
    buttons = []
    is_owner = (current_user_id == BOT_OWNER_ID)

    for adm in admins:
        uid = adm["user_id"]
        name = adm.get("full_name") or f"Admin {uid}"
        is_supreme = (uid == BOT_OWNER_ID)

        if is_supreme:
            buttons.append([
                InlineKeyboardButton(text=f"👑 Bosh Ega: {name} ({uid})", callback_data="noop")
            ])
        else:
            row = [InlineKeyboardButton(text=f"👤 {name} ({uid})", callback_data="noop")]
            # Only the Supreme Bot Owner (618430308) can remove other admins
            if is_owner:
                row.append(InlineKeyboardButton(text="🗑 Chiqarish", callback_data=f"deladmin:{uid}"))
            buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="➕ Yangi Admin qo'shish", callback_data="add_admin")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
