from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import datetime
import database as db
from keyboards.reply import get_main_keyboard, get_cancel_keyboard
from keyboards.inline import get_withdraw_presets_keyboard, get_order_admin_keyboard

router = Router()

class WithdrawState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_target = State()

async def check_ban(message_or_call) -> bool:
    user_id = message_or_call.from_user.id
    user = await db.get_user(user_id)
    if user and user.get("is_banned") == 1:
        if isinstance(message_or_call, Message):
            await message_or_call.answer("🚫 <b>Siz botdan bloklangansiz!</b>", parse_mode="HTML")
        elif isinstance(message_or_call, CallbackQuery):
            await message_or_call.answer("🚫 Siz botdan bloklangansiz!", show_alert=True)
        return True
    return False

# Entry point: "⭐ Stars yechish"
@router.message(F.text == "⭐ Stars yechish")
async def msg_withdraw_start(message: Message, state: FSMContext):
    if await check_ban(message):
        return

    await state.clear()
    user_id = message.from_user.id
    await db.touch_user_activity(user_id)
    user = await db.get_user(user_id)
    if not user:
        user, _ = await db.add_or_update_user(user_id, message.from_user.full_name, message.from_user.username or "")

    balance = user.get("balance", 0.0)
    min_withdraw = float(await db.get_setting("min_withdraw", "15"))
    display_balance = int(balance) if balance.is_integer() else f"{balance:.1f}"
    display_min = int(min_withdraw) if min_withdraw.is_integer() else f"{min_withdraw:.1f}"

    if balance < min_withdraw:
        await message.answer(
            f"❌ <b>Stars yechib olish uchun hisobingizda kamida {display_min} ⭐ bo'lishi kerak!</b>\n\n"
            f"💰 Sizning balansingiz: <b>{display_balance} ⭐</b>\n\n"
            f"Do'stlaringizni taklif qilib, balansingizni to'ldiring! 🚀",
            parse_mode="HTML"
        )
        return

    text = (
        f"⭐ <b>Stars yechib olish</b>\n\n"
        f"💰 Balansingiz: <b>{display_balance} ⭐</b>\n"
        f"⚡ Minimal yechish: <b>{display_min} ⭐</b>\n\n"
        f"Quyidagi miqdorlardan birini tanlang:"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_withdraw_presets_keyboard()
    )

# Callback handler for preset selection
@router.callback_query(F.data.startswith("withdraw:"))
async def callback_preset_selected(call: CallbackQuery, state: FSMContext):
    if await check_ban(call):
        return

    action = call.data.split(":")[1]
    user_id = call.from_user.id
    is_admin = await db.is_user_admin(user_id)

    if action == "cancel":
        await state.clear()
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer("❌ Yechib olish bekor qilindi.", reply_markup=get_main_keyboard(is_admin))
        return

    try:
        amount = float(action)
    except ValueError:
        await call.answer("Xatolik yuz berdi!", show_alert=True)
        return

    user = await db.get_user(user_id)
    balance = user.get("balance", 0.0) if user else 0.0

    if balance < amount:
        display_amt = int(amount) if amount.is_integer() else amount
        display_bal = int(balance) if balance.is_integer() else f"{balance:.1f}"
        await call.answer(
            f"❌ Balansingizda {display_amt} ⭐ mavjud emas! (Sizda: {display_bal} ⭐)",
            show_alert=True
        )
        return

    display_amt = int(amount) if amount.is_integer() else amount
    await state.update_data(withdraw_amount=amount)
    await state.set_state(WithdrawState.waiting_for_target)

    try:
        await call.message.delete()
    except Exception:
        pass

    prompt_text = (
        f"💸 Tanlangan miqdor: <b>{display_amt} ⭐</b>\n\n"
        f"Iltimos, Stars yuborilishi kerak bo'lgan Telegram <b>username</b>ingizni yoki kanal/post havolangizni yuboring:\n"
        f"<i>(Masalan: <code>@{call.from_user.username or 'username'}</code> yoki <code>https://t.me/kanal/123</code>)</i>\n\n"
        f"Bekor qilish uchun pastdagi tugmani bosing."
    )

    await call.message.answer(
        prompt_text,
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

# Receive target address
@router.message(WithdrawState.waiting_for_target)
async def process_withdraw_target(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    is_admin = await db.is_user_admin(user_id)

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Yechish so'rovi bekor qilindi.", reply_markup=get_main_keyboard(is_admin))
        return

    target = message.text.strip()
    if len(target) < 3 or len(target) > 150:
        await message.answer("⚠️ Iltimos, to'g'ri username yoki havola kiriting (kamida 3 ta belgi).")
        return

    data = await state.get_data()
    amount = data.get("withdraw_amount")
    if not amount:
        await state.clear()
        await message.answer("Xatolik yuz berdi. Qaytadan urinib ko'ring.", reply_markup=get_main_keyboard(is_admin))
        return

    order_id = await db.create_withdrawal_order(user_id, amount, target)
    if not order_id:
        await state.clear()
        await message.answer(
            "❌ Balansingizda yetarli Stars qolmagan yoki xatolik yuz berdi.",
            reply_markup=get_main_keyboard(is_admin)
        )
        return

    await state.clear()
    display_amt = int(amount) if amount.is_integer() else amount

    # Confirm to user
    await message.answer(
        f"✅ <b>So'rovingiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"🆔 Buyurtma raqami: <b>#{order_id}</b>\n"
        f"⭐ Miqdor: <b>{display_amt} ⭐</b>\n"
        f"🎯 Manzil: <code>{target}</code>\n\n"
        f"⏳ Adminlarimiz tez orada Starsni jo'natishadi. «📋 So'rovlarim» bo'limida holatni kuzatib borishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(is_admin)
    )

    # Notify all admins dynamically from DB
    admins = await db.get_all_admins()
    user_mention = f"<a href='tg://user?id={user_id}'>{message.from_user.full_name}</a>"
    username_str = f"@{message.from_user.username}" if message.from_user.username else "Yo'q"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    admin_notification = (
        f"🔔 <b>Yangi Stars yechish so'rovi!</b>\n\n"
        f"🆔 Buyurtma: <b>#{order_id}</b>\n"
        f"👤 Foydalanuvchi: {user_mention} ({username_str})\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"⭐ Miqdor: <b>{display_amt} ⭐</b>\n"
        f"🎯 Manzil / Akkaunt: <code>{target}</code>\n"
        f"⏰ Vaqt: <i>{now_str}</i>"
    )

    for adm in admins:
        try:
            await bot.send_message(
                adm["user_id"],
                admin_notification,
                parse_mode="HTML",
                reply_markup=get_order_admin_keyboard(order_id)
            )
        except Exception:
            pass
