from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
import database as db
from keyboards.reply import get_main_keyboard
from keyboards.inline import get_share_keyboard, get_sub_channels_keyboard
from utils.subscription import check_user_subscription

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, bot: Bot, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username or ""

    # Parse referral parameter
    referred_by = None
    args = command.args
    if args:
        ref_str = args.replace("ref", "").strip()
        if ref_str.isdigit():
            referred_by = int(ref_str)

    # Check mandatory channels
    is_subbed, unjoined = await check_user_subscription(bot, user_id)
    if not is_subbed:
        # Save referrer in state so we can reward when they finish subscription
        if referred_by:
            await state.update_data(referred_by=referred_by)
        kb = get_sub_channels_keyboard(unjoined)
        await message.answer(
            "⚠️ <b>Botdan to'liq foydalanish uchun quyidagi rasmiy kanallarga a'zo bo'ling:</b>\n\n"
            "A'zo bo'lgach, <b>«✅ Tekshirish»</b> tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=kb
        )
        return

    # User is subscribed, register in DB
    user_data, is_new = await db.add_or_update_user(user_id, full_name, username, referred_by)

    # If new user and referred by someone
    if is_new and user_data.get("referred_by"):
        ref_id = user_data["referred_by"]
        ref_bonus = float(await db.get_setting("ref_bonus", "2"))
        await db.reward_referrer(ref_id, ref_bonus)
        try:
            await bot.send_message(
                ref_id,
                f"🎉 <b>Yangi do'stingiz qo'shildi!</b>\n\n"
                f"👤 Do'stingiz: {full_name}\n"
                f"⭐ Sizga <b>+{int(ref_bonus) if ref_bonus.is_integer() else ref_bonus} ⭐</b> berildi!",
                parse_mode="HTML"
            )
        except Exception:
            pass

    welcome_text = (
        f"👋 <b>Assalomu alaykum, {full_name}!</b>\n\n"
        f"🌟 <b>Pro Stars Bot</b>ga xush kelibsiz!\n"
        f"Bu yerda do'stlaringizni taklif qilib, bepul <b>Telegram Stars</b> to'plashingiz va o'z hisobingizga yechib olishingiz mumkin.\n\n"
        f"👇 Kerakli bo'limni tanlang:"
    )

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(user_id)
    )

@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    full_name = call.from_user.full_name
    username = call.from_user.username or ""

    is_subbed, unjoined = await check_user_subscription(bot, user_id)
    if not is_subbed:
        await call.answer("❌ Hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)
        kb = get_sub_channels_keyboard(unjoined)
        try:
            await call.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            pass
        return

    await call.answer("✅ Rahmat, a'zolik tasdiqlandi!")
    data = await state.get_data()
    referred_by = data.get("referred_by")
    await state.clear()

    user_data, is_new = await db.add_or_update_user(user_id, full_name, username, referred_by)
    if is_new and user_data.get("referred_by"):
        ref_id = user_data["referred_by"]
        ref_bonus = float(await db.get_setting("ref_bonus", "2"))
        await db.reward_referrer(ref_id, ref_bonus)
        try:
            await bot.send_message(
                ref_id,
                f"🎉 <b>Yangi do'stingiz qo'shildi!</b>\n\n"
                f"👤 Do'stingiz: {full_name}\n"
                f"⭐ Sizga <b>+{int(ref_bonus) if ref_bonus.is_integer() else ref_bonus} ⭐</b> berildi!",
                parse_mode="HTML"
            )
        except Exception:
            pass

    try:
        await call.message.delete()
    except Exception:
        pass

    await call.message.answer(
        f"👋 <b>Xush kelibsiz, {full_name}!</b>\n\n"
        f"🌟 Bepul Telegram Stars ishlashni boshlash uchun quyidagi tugmalardan foydalaning:",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(user_id)
    )

# ⭐ Stars ishlash
@router.message(F.text == "⭐ Stars ishlash")
async def msg_stars_earn(message: Message, bot: Bot):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    ref_bonus = await db.get_setting("ref_bonus", "2")

    ref_link = f"https://t.me/{bot_info.username}?start=ref{user_id}"

    text = (
        f"⭐ <b>Stars ishlash</b>\n\n"
        f"Har bir to'liq ro'yxatdan o'tgan do'stingiz uchun sizga <b>{ref_bonus} ⭐</b> beriladi.\n\n"
        f"🔗 <b>Sizning referal havolangiz:</b>\n"
        f"<code>{ref_link}</code>"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_share_keyboard(bot_info.username, user_id, ref_bonus)
    )

# 👤 Hisobim
@router.message(F.text == "👤 Hisobim")
async def msg_profile(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        user, _ = await db.add_or_update_user(user_id, message.from_user.full_name, message.from_user.username or "")

    balance = user.get("balance", 0.0)
    display_balance = int(balance) if balance.is_integer() else f"{balance:.1f}"
    withdrawn = user.get("total_withdrawn", 0.0)
    display_withdrawn = int(withdrawn) if withdrawn.is_integer() else f"{withdrawn:.1f}"

    text = (
        f"👤 <b>Foydalanuvchi hisobi</b>\n\n"
        f"🆔 Sizning ID: <code>{user_id}</code>\n"
        f"👤 Ism: <b>{message.from_user.full_name}</b>\n"
        f"💰 Balansingiz: <b>{display_balance} ⭐</b>\n"
        f"👥 Taklif qilgan do'stlaringiz: <b>{user.get('referrals_count', 0)} ta</b>\n"
        f"💸 Jami yechib olingan: <b>{display_withdrawn} ⭐</b>"
    )

    await message.answer(text, parse_mode="HTML")

# 📋 So'rovlarim
@router.message(F.text == "📋 So'rovlarim")
async def msg_my_orders(message: Message):
    user_id = message.from_user.id
    orders = await db.get_user_orders(user_id, limit=10)

    if not orders:
        await message.answer(
            "📋 <b>Sizda hali Stars yechib olish so'rovlari mavjud emas.</b>\n\n"
            "Do'stlaringizni taklif qilib, hisobingizda 15 ⭐ to'plang va yechib oling!",
            parse_mode="HTML"
        )
        return

    text = "📋 <b>Sizning so'nggi yechish so'rovlaringiz:</b>\n\n"
    status_icons = {
        "pending": "⏳ Kutilmoqda",
        "approved": "✅ To'lab berildi",
        "rejected": "❌ Rad etildi"
    }

    for order in orders:
        st = status_icons.get(order["status"], order["status"])
        amt = int(order["amount"]) if float(order["amount"]).is_integer() else order["amount"]
        text += (
            f"🔹 <b>Buyurtma #{order['id']}</b>\n"
            f"   Miqdor: <b>{amt} ⭐</b>\n"
            f"   Manzil: <code>{order['target_account']}</code>\n"
            f"   Holat: <b>{st}</b>\n"
            f"   Sana: <i>{order['created_at']}</i>\n"
        )
        if order.get("reject_reason"):
            text += f"   Sabab: <i>{order['reject_reason']}</i>\n"
        text += "\n"

    await message.answer(text, parse_mode="HTML")

# 📖 Qo'llanma
@router.message(F.text == "📖 Qo'llanma")
async def msg_guide(message: Message):
    ref_bonus = await db.get_setting("ref_bonus", "2")
    min_withdraw = await db.get_setting("min_withdraw", "15")

    text = (
        f"📖 <b>Botdan foydalanish qo'llanmasi</b>\n\n"
        f"1️⃣ <b>Stars ishlash:</b>\n"
        f"«⭐ Stars ishlash» tugmasini bosing va shaxsiy referal havolangizni nusxalang. Uni do'stlaringizga, guruhlarga yoki kanallarga tarqating.\n\n"
        f"2️⃣ <b>Mukofot:</b>\n"
        f"Havolangiz orqali botga kirgan har bir do'stingiz uchun sizga <b>{ref_bonus} ⭐</b> beriladi.\n\n"
        f"3️⃣ <b>Stars yechib olish:</b>\n"
        f"Hisobingizda minimal <b>{min_withdraw} ⭐</b> to'planganda, «⭐ Stars yechish» bo'limi orqali buyurtma bera olasiz.\n\n"
        f"4️⃣ <b>Yetkazib berish:</b>\n"
        f"Yechish so'rovi yuborilgach, adminlarimiz uni tekshirib, Starsni Telegram profilingizga (sovg'a) yoki kanalingiz postiga reaksiya sifatida yuboradi.\n\n"
        f"❓ Savollar bo'lsa, adminlarimizga murojaat qilishingiz mumkin."
    )

    await message.answer(text, parse_mode="HTML")
