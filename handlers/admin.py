from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
from config import ADMINS
import database as db
from keyboards.reply import get_admin_keyboard, get_main_keyboard, get_cancel_keyboard
from keyboards.inline import get_order_admin_keyboard, get_admin_channels_keyboard

router = Router()

class AdminStates(StatesGroup):
    waiting_for_ref_bonus = State()
    waiting_for_broadcast = State()
    waiting_for_broadcast_confirm = State()
    waiting_for_channel = State()
    waiting_for_balance_target = State()
    waiting_for_balance_amount = State()
    waiting_for_reject_reason = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# Admin entry points
@router.message(Command("admin"))
@router.message(F.text == "⚙️ Admin Panel")
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await message.answer(
        "🛠 <b>Admin Boshqaruv Paneliga xush kelibsiz!</b>\n\n"
        "Kerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )

@router.message(F.text == "🔙 Asosiy menyu")
async def cmd_back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Asosiy menyuga qaytdingiz.",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

# 📊 Statistika
@router.message(F.text == "📊 Statistika")
async def msg_admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    stats = await db.get_stats()
    ref_bonus = await db.get_setting("ref_bonus", "2")
    min_withdraw = await db.get_setting("min_withdraw", "15")

    text = (
        "📊 <b>Bot Statistikasi:</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']:,} ta</b>\n"
        f"🆕 Bugun qo'shilganlar: <b>{stats['today_users']:,} ta</b>\n\n"
        f"📦 Jami yechish so'rovlari: <b>{stats['total_orders']:,} ta</b>\n"
        f"⏳ Kutilayotgan so'rovlar: <b>{stats['pending_orders']:,} ta</b>\n"
        f"✅ To'lab berilgan: <b>{stats['approved_orders']:,} ta</b>\n"
        f"❌ Rad etilgan: <b>{stats['rejected_orders']:,} ta</b>\n\n"
        f"💸 Jami to'langan Stars: <b>{stats['sum_withdrawn']:,.1f} ⭐</b>\n"
        f"💰 Userlar balansidagi Stars: <b>{stats['sum_balances']:,.1f} ⭐</b>\n\n"
        f"⚙️ <b>Hozirgi sozlamalar:</b>\n"
        f"• Har 1 do'st uchun: <b>{ref_bonus} ⭐</b>\n"
        f"• Minimal yechish: <b>{min_withdraw} ⭐</b>"
    )

    await message.answer(text, parse_mode="HTML")

# 📥 So'rovlar (Pending orders)
@router.message(F.text == "📥 So'rovlar")
async def msg_admin_pending_orders(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    orders = await db.get_pending_orders(limit=10)
    if not orders:
        await message.answer("✅ Hozirda yangi kutilayotgan so'rovlar yo'q!")
        return

    await message.answer(f"📥 <b>Kutilayotgan so'rovlar soni: {len(orders)} ta</b> (ko'pi bilan 10 tasi ko'rsatilmoqda):", parse_mode="HTML")

    for order in orders:
        amt = int(order["amount"]) if float(order["amount"]).is_integer() else order["amount"]
        user_name = order.get("full_name", "Foydalanuvchi")
        username_str = f"@{order['username']}" if order.get("username") else "Yo'q"
        text = (
            f"🆔 <b>Buyurtma #{order['id']}</b>\n"
            f"👤 Foydalanuvchi: <a href='tg://user?id={order['user_id']}'>{user_name}</a> ({username_str})\n"
            f"🆔 ID: <code>{order['user_id']}</code>\n"
            f"⭐ Miqdor: <b>{amt} ⭐</b>\n"
            f"🎯 Manzil: <code>{order['target_account']}</code>\n"
            f"⏰ Sana: <i>{order['created_at']}</i>"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=get_order_admin_keyboard(order["id"]))

# Order Approve Callback
@router.callback_query(F.data.startswith("order:approve:"))
async def cb_approve_order(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan!", show_alert=True)
        return

    order_id = int(call.data.split(":")[2])
    order = await db.get_order(order_id)
    if not order:
        await call.answer("Buyurtma topilmadi!", show_alert=True)
        return

    if order["status"] != "pending":
        await call.answer(f"Bu buyurtma allaqachon ko'rib chiqilgan ({order['status']})!", show_alert=True)
        return

    updated = await db.update_order_status(order_id, "approved")
    if updated:
        admin_name = call.from_user.full_name
        amt = int(order["amount"]) if float(order["amount"]).is_integer() else order["amount"]
        try:
            await call.message.edit_text(
                f"{call.message.html_text}\n\n✅ <b>TO'LAB BERILDI</b>\nTasdiqladi: {admin_name}",
                parse_mode="HTML",
                reply_markup=None
            )
        except Exception:
            pass

        # Notify user
        try:
            await bot.send_message(
                order["user_id"],
                f"🎉 <b>Buyurtmangiz tasdiqlandi!</b>\n\n"
                f"🆔 Buyurtma: <b>#{order_id}</b>\n"
                f"⭐ Miqdor: <b>{amt} ⭐</b>\n"
                f"🎯 Manzil: <code>{order['target_account']}</code>\n\n"
                f"Stars hisobingizga muvaffaqiyatli yetkazildi! Xizmatimizdan foydalanganingiz uchun rahmat!",
                parse_mode="HTML"
            )
        except Exception:
            pass

        await call.answer("✅ Buyurtma tasdiqlandi!")

# Order Reject Callback
@router.callback_query(F.data.startswith("order:reject:"))
async def cb_reject_order(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan!", show_alert=True)
        return

    order_id = int(call.data.split(":")[2])
    order = await db.get_order(order_id)
    if not order or order["status"] != "pending":
        await call.answer("Buyurtma topilmadi yoki allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await state.update_data(reject_order_id=order_id, reject_msg_id=call.message.message_id, reject_chat_id=call.message.chat.id)
    await state.set_state(AdminStates.waiting_for_reject_reason)

    await call.message.answer(
        f"⚠️ <b>#{order_id} raqamli so'rovni rad etish sababini yozing:</b>\n"
        f"<i>(Foydalanuvchiga ushbu sabab yuboriladi va {order['amount']} ⭐ uning balansiga qaytariladi).</i>\n\n"
        f"Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(AdminStates.waiting_for_reject_reason)
async def process_reject_reason(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    reason = message.text.strip()
    data = await state.get_data()
    order_id = data.get("reject_order_id")
    await state.clear()

    order = await db.get_order(order_id)
    if not order or order["status"] != "pending":
        await message.answer("Buyurtma topilmadi yoki allaqachon yakunlangan.", reply_markup=get_admin_keyboard())
        return

    updated = await db.update_order_status(order_id, "rejected", reject_reason=reason)
    if updated:
        admin_name = message.from_user.full_name
        amt = int(order["amount"]) if float(order["amount"]).is_integer() else order["amount"]

        await message.answer(
            f"❌ <b>Buyurtma #{order_id} rad etildi.</b>\n"
            f"Sabab: <i>{reason}</i>\n"
            f"⭐ {amt} Stars foydalanuvchi hisobiga qaytarildi.",
            parse_mode="HTML",
            reply_markup=get_admin_keyboard()
        )

        # Notify user
        try:
            await bot.send_message(
                order["user_id"],
                f"❌ <b>Sizning Stars yechish so'rovingiz rad etildi.</b>\n\n"
                f"🆔 Buyurtma: <b>#{order_id}</b>\n"
                f"⭐ Miqdor: <b>{amt} ⭐</b>\n"
                f"⚠️ Sabab: <i>{reason}</i>\n\n"
                f"Stars hisobingizga qaytarildi. Iltimos, ma'lumotlarni to'g'ri kiritib qaytadan urinib ko'ring.",
                parse_mode="HTML"
            )
        except Exception:
            pass

# 💰 Referal narxini sozlash
@router.message(F.text == "💰 Referal narxini sozlash")
async def msg_admin_change_ref(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    current = await db.get_setting("ref_bonus", "2")
    await state.set_state(AdminStates.waiting_for_ref_bonus)
    await message.answer(
        f"💰 <b>Hozirda har bir do'st uchun: {current} ⭐ beriladi.</b>\n\n"
        f"Yangi qiymatni kiriting (masalan: <code>1</code>, <code>2</code>, <code>5</code>, <code>10</code>):\n\n"
        f"Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

@router.message(AdminStates.waiting_for_ref_bonus)
async def process_ref_bonus(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    text = message.text.strip().replace(",", ".")
    try:
        new_val = float(text)
        if new_val <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Iltimos, 0 dan katta to'g'ri son kiriting (masalan: 1 yoki 2).")
        return

    val_str = str(int(new_val)) if new_val.is_integer() else str(new_val)
    await db.set_setting("ref_bonus", val_str)
    await state.clear()

    await message.answer(
        f"✅ <b>Muvaffaqiyatli saqlandi!</b>\nEndi har bir taklif qilingan do'st uchun <b>{val_str} ⭐</b> beriladi.",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )

# 📢 Kanallar (Majburiy obuna)
@router.message(F.text == "📢 Kanallar")
async def msg_admin_channels(message: Message):
    if not is_admin(message.from_user.id):
        return

    channels = await db.get_channels()
    text = (
        "📢 <b>Majburiy a'zolik kanallari:</b>\n\n"
        "Foydalanuvchilar botga kirganda quyidagi kanallarga obuna bo'lishi talab qilinadi.\n"
        f"Jami kanallar: <b>{len(channels)} ta</b>\n"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_channels_keyboard(channels))

@router.callback_query(F.data == "add_channel")
async def cb_add_channel(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_channel)
    await call.message.answer(
        "📢 <b>Kanal qo'shish uchun quyidagi formatda yuboring:</b>\n\n"
        "<code>@kanal_usernomi Havola Kanal_Nomi</code>\n\n"
        "Masalan:\n"
        "<code>@stars_uz https://t.me/stars_uz Rasmiy Kanal</code>\n\n"
        "⚠️ <i>Muhim: Botni ushbu kanalga admin qilib qo'yishingiz kerak!</i>\n"
        "Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(AdminStates.waiting_for_channel)
async def process_add_channel(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    parts = message.text.strip().split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("⚠️ Noto'g'ri format. Iltimos: <code>@kanal https://t.me/kanal Kanal Nomi</code> ko'rinishida yuboring.", parse_mode="HTML")
        return

    channel_id = parts[0].strip()
    invite_link = parts[1].strip()
    title = parts[2].strip() if len(parts) > 2 else channel_id

    # Verify bot can access the channel
    try:
        chat = await bot.get_chat(channel_id)
        if chat.title:
            title = chat.title
    except Exception as e:
        await message.answer(f"⚠️ Bot ushbu kanalga ulanolmadi. Botni kanalga admin qildingizmi?\nXato: {e}")
        return

    success = await db.add_channel(channel_id, title, invite_link)
    await state.clear()

    if success:
        await message.answer(f"✅ <b>{title}</b> kanali muvaffaqiyatli qo'shildi!", parse_mode="HTML", reply_markup=get_admin_keyboard())
    else:
        await message.answer("❌ Kanalni qo'shishda xatolik yuz berdi.", reply_markup=get_admin_keyboard())

@router.callback_query(F.data.startswith("delchan:"))
async def cb_delete_channel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    channel_id = call.data.split("delchan:")[1]
    await db.delete_channel(channel_id)
    await call.answer(f"{channel_id} o'chirildi!")

    channels = await db.get_channels()
    try:
        await call.message.edit_reply_markup(reply_markup=get_admin_channels_keyboard(channels))
    except Exception:
        pass

# ✉️ Xabar yuborish (Broadcast)
@router.message(F.text == "✉️ Xabar yuborish")
async def msg_admin_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_broadcast)
    await message.answer(
        "✉️ <b>Barcha bot foydalanuvchilariga yubormoqchi bo'lgan xabaringizni yuboring:</b>\n\n"
        "<i>(Matn, rasm, video, havola bo'lishi mumkin)</i>\n\n"
        "Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

@router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    await state.clear()
    status_msg = await message.answer("⏳ Xabar tarqatish boshlandi...")

    user_ids = await db.get_all_user_ids()
    total = len(user_ids)
    success = 0
    failed = 0

    for uid in user_ids:
        try:
            await message.copy_to(chat_id=uid)
            success += 1
            await asyncio.sleep(0.05)  # Telegram limits protection
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"👥 Jami qabul qiluvchilar: <b>{total} ta</b>\n"
        f"✅ Muvaffaqiyatli yetib bordi: <b>{success} ta</b>\n"
        f"❌ Yetib bormadi (bloklaganlar): <b>{failed} ta</b>",
        parse_mode="HTML"
    )

# 👤 User balansi (Add / Subtract Stars)
@router.message(F.text == "👤 User balansi")
async def msg_user_balance(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_balance_target)
    await message.answer(
        "👤 <b>Foydalanuvchi balansini o'zgartirish</b>\n\n"
        "Foydalanuvchining Telegram ID raqamini kiriting:\n\n"
        "Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

@router.message(AdminStates.waiting_for_balance_target)
async def process_balance_target(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    if not message.text.strip().isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamdan iborat Telegram ID kiriting.")
        return

    target_id = int(message.text.strip())
    user = await db.get_user(target_id)
    if not user:
        await message.answer("❌ Bu ID dagi foydalanuvchi bot bazasida topilmadi.")
        return

    await state.update_data(target_id=target_id)
    await state.set_state(AdminStates.waiting_for_balance_amount)

    cur_bal = user.get("balance", 0.0)
    await message.answer(
        f"👤 Topildi: <b>{user.get('full_name')}</b>\n"
        f"💰 Hozirgi balansi: <b>{cur_bal} ⭐</b>\n\n"
        f"Qo'shmoqchi yoki ayirmoqchi bo'lgan miqdorni kiriting:\n"
        f"<i>(Masalan: <code>+50</code> yoki <code>-20</code>)</i>",
        parse_mode="HTML"
    )

@router.message(AdminStates.waiting_for_balance_amount)
async def process_balance_amount(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    data = await state.get_data()
    target_id = data.get("target_id")
    await state.clear()

    try:
        val = float(message.text.replace("+", "").strip())
        if message.text.strip().startswith("-"):
            delta = -abs(val)
        else:
            delta = abs(val)
    except ValueError:
        await message.answer("⚠️ Noto'g'ri son formati.", reply_markup=get_admin_keyboard())
        return

    ok = await db.update_user_balance(target_id, delta)
    if not ok:
        await message.answer("❌ Foydalanuvchi balansida yetarli mablag' yo'q (manfiy bo'lib ketishi mumkin emas).", reply_markup=get_admin_keyboard())
        return

    user = await db.get_user(target_id)
    new_bal = user.get("balance", 0.0)
    sign = "+" if delta > 0 else ""
    await message.answer(
        f"✅ <b>Balans muvaffaqiyatli o'zgartirildi!</b>\n"
        f"ID: <code>{target_id}</code>\n"
        f"O'zgarish: <b>{sign}{delta} ⭐</b>\n"
        f"Yangi balans: <b>{new_bal} ⭐</b>",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )

    try:
        await bot.send_message(
            target_id,
            f"ℹ️ <b>Sizning balansingiz admin tomonidan yangilandi:</b>\n"
            f"O'zgarish: <b>{sign}{delta} ⭐</b>\n"
            f"Hozirgi balansingiz: <b>{new_bal} ⭐</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass
