import random
import string
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import BOT_OWNER_ID
import database as db
from keyboards.reply import get_admin_keyboard, get_main_keyboard, get_cancel_keyboard
from keyboards.inline import (
    get_order_admin_keyboard,
    get_admin_channels_keyboard,
    get_users_mgmt_keyboard,
    get_user_actions_keyboard,
    get_admins_mgmt_keyboard,
    get_promocodes_mgmt_keyboard,
    get_promo_auto_keyboard
)

router = Router()

class AdminStates(StatesGroup):
    waiting_for_ref_bonus = State()
    waiting_for_broadcast = State()
    waiting_for_channel = State()
    waiting_for_user_search = State()
    waiting_for_balance_amount = State()
    waiting_for_dm_message = State()
    waiting_for_reject_reason = State()
    waiting_for_new_admin_id = State()
    waiting_for_promo_code = State()
    waiting_for_promo_reward = State()
    waiting_for_promo_limit = State()

# Entry points: /admin or "⚙️ Admin Panel"
@router.message(Command("admin"))
@router.message(F.text == "⚙️ Admin Panel")
async def cmd_admin(message: Message, state: FSMContext):
    if not await db.is_user_admin(message.from_user.id):
        return

    await state.clear()
    await message.answer(
        "🛠 <b>Admin Boshqaruv Paneliga xush kelibsiz!</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )

@router.message(F.text == "🔙 Asosiy menyu")
async def cmd_back_to_main(message: Message, state: FSMContext):
    await state.clear()
    is_admin = await db.is_user_admin(message.from_user.id)
    await message.answer(
        "Asosiy menyuga qaytdingiz.",
        reply_markup=get_main_keyboard(is_admin)
    )

# ==================== 📊 STATISTIKA ====================
@router.message(F.text == "📊 Statistika")
async def msg_admin_stats(message: Message):
    if not await db.is_user_admin(message.from_user.id):
        return

    stats = await db.get_stats()
    ref_bonus = await db.get_setting("ref_bonus", "2")
    min_withdraw = await db.get_setting("min_withdraw", "15")

    text = (
        "📊 <b>Umumiy Bot Statistikasi:</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']:,} ta</b>\n"
        f"⚡ 24 soat ichida faol: <b>{stats['active_users_24h']:,} ta</b>\n"
        f"📅 7 kun ichida faol: <b>{stats['active_users_7d']:,} ta</b>\n"
        f"🆕 Bugun qo'shilganlar: <b>{stats['today_users']:,} ta</b>\n"
        f"🚫 Bloklanganlar: <b>{stats['banned_users']:,} ta</b>\n\n"
        f"📦 Jami yechish so'rovlari: <b>{stats['total_orders']:,} ta</b>\n"
        f"⏳ Kutilayotgan so'rovlar: <b>{stats['pending_orders']:,} ta</b>\n"
        f"✅ To'lab berilgan: <b>{stats['approved_orders']:,} ta</b>\n"
        f"❌ Rad etilgan: <b>{stats['rejected_orders']:,} ta</b>\n\n"
        f"💸 Jami to'langan Stars: <b>{stats['sum_withdrawn']:,.1f} ⭐</b>\n"
        f"💰 Userlar hisobidagi Stars: <b>{stats['sum_balances']:,.1f} ⭐</b>\n\n"
        f"👑 Adminlar soni: <b>{stats['admins_count']} ta</b>\n"
        f"💰 Referal narxi: <b>{ref_bonus} ⭐</b> | Min. yechish: <b>{min_withdraw} ⭐</b>"
    )

    await message.answer(text, parse_mode="HTML")

# ==================== 👥 FOYDALANUVCHILAR BOSHQARUVI ====================
@router.message(F.text == "👥 Foydalanuvchilar")
async def msg_admin_users(message: Message):
    if not await db.is_user_admin(message.from_user.id):
        return

    stats = await db.get_detailed_user_stats()

    text = (
        "👥 <b>Foydalanuvchilar Boshqaruvi:</b>\n\n"
        f"📊 Jami foydalanuvchilar: <b>{stats['total_users']:,} ta</b>\n"
        f"⚡ Faol foydalanuvchilar (24 soat): <b>{stats['active_users_24h']:,} ta</b>\n"
        f"📅 Faol foydalanuvchilar (7 kun): <b>{stats['active_users_7d']:,} ta</b>\n"
        f"🆕 Bugun qo'shilgan: <b>{stats['today_users']:,} ta</b>\n"
        f"🚫 Bloklanganlar: <b>{stats['banned_users']:,} ta</b>\n"
        f"👥 Jami taklif qilingan referallar: <b>{stats['total_referrals']:,} ta</b>\n\n"
        f"💰 Hozirgi userlar balansi: <b>{stats['sum_balances']:,.1f} ⭐</b>\n"
        f"💸 Jami yechib olingan: <b>{stats['sum_withdrawn']:,.1f} ⭐</b>\n\n"
        "Quyidagi amallardan birini tanlang:"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=get_users_mgmt_keyboard())

# Top 10 Referrers Callback
@router.callback_query(F.data == "users:top_referrers")
async def cb_top_referrers(call: CallbackQuery):
    if not await db.is_user_admin(call.from_user.id):
        return

    top = await db.get_top_referrers(limit=10)
    if not top:
        await call.answer("Hozircha referal taklif qilganlar yo'q.", show_alert=True)
        return

    text = "🏆 <b>Eng ko'p referal taklif qilgan Top 10 foydalanuvchi:</b>\n\n"
    for i, u in enumerate(top, 1):
        uname = f"@{u['username']}" if u.get("username") else "Yo'q"
        name = u.get("full_name") or "Foydalanuvchi"
        text += (
            f"<b>{i}.</b> <a href='tg://user?id={u['user_id']}'>{name}</a> ({uname})\n"
            f"   🆔 ID: <code>{u['user_id']}</code>\n"
            f"   👥 Taklif qilgan: <b>{u['referrals_count']} ta</b> | 💰 Balans: <b>{u['balance']} ⭐</b>\n\n"
        )

    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

# Recent Users Callback
@router.callback_query(F.data == "users:recent")
async def cb_recent_users(call: CallbackQuery):
    if not await db.is_user_admin(call.from_user.id):
        return

    recent = await db.get_recent_users(limit=10)
    if not recent:
        await call.answer("Foydalanuvchilar topilmadi.", show_alert=True)
        return

    text = "🆕 <b>So'nggi qo'shilgan 10 ta foydalanuvchi:</b>\n\n"
    for i, u in enumerate(recent, 1):
        uname = f"@{u['username']}" if u.get("username") else "Yo'q"
        name = u.get("full_name") or "Foydalanuvchi"
        text += (
            f"<b>{i}.</b> <a href='tg://user?id={u['user_id']}'>{name}</a> ({uname})\n"
            f"   🆔 ID: <code>{u['user_id']}</code> | 💰 Balans: <b>{u['balance']} ⭐</b>\n"
            f"   ⏰ Sana: <i>{u['joined_at']}</i>\n\n"
        )

    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

# Search User Callback & State
@router.callback_query(F.data == "users:search")
async def cb_search_user(call: CallbackQuery, state: FSMContext):
    if not await db.is_user_admin(call.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_user_search)
    await call.message.answer(
        "🔍 <b>Foydalanuvchini qidirish:</b>\n\n"
        "Foydalanuvchining <b>Telegram ID</b> raqamini yoki <b>@username</b>ini kiriting:\n\n"
        "Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(AdminStates.waiting_for_user_search)
async def process_user_search(message: Message, state: FSMContext):
    if not await db.is_user_admin(message.from_user.id):
        return

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    query = message.text.strip()
    user = await db.search_user(query)

    if not user:
        await message.answer(
            f"❌ «{query}» bo'yicha foydalanuvchi topilmadi!\nQaytadan kiriting yoki «❌ Bekor qilish» deb yozing."
        )
        return

    await state.clear()
    uid = user["user_id"]
    status_str = "🚫 Bloklangan" if user.get("is_banned") == 1 else "✅ Faol"
    uname_str = f"@{user['username']}" if user.get("username") else "Mavjud emas"
    ref_by_str = f"<code>{user['referred_by']}</code>" if user.get("referred_by") else "Hech kim"

    info_text = (
        f"👤 <b>Foydalanuvchi Ma'lumotlari:</b>\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"👤 Ism: <b>{user.get('full_name')}</b>\n"
        f"🔗 Username: {uname_str}\n"
        f"💰 Balans: <b>{user.get('balance', 0.0)} ⭐</b>\n"
        f"👥 Taklif qilgan: <b>{user.get('referrals_count', 0)} ta</b>\n"
        f"🤝 Kim taklif qilgan: {ref_by_str}\n"
        f"💸 Jami yechib olgan: <b>{user.get('total_withdrawn', 0.0)} ⭐</b>\n"
        f"🛡 Holat: <b>{status_str}</b>\n"
        f"📅 Qo'shilgan: <i>{user.get('joined_at')}</i>\n"
        f"⚡ Oxirgi faollik: <i>{user.get('last_active')}</i>"
    )

    await message.answer(
        info_text,
        parse_mode="HTML",
        reply_markup=get_user_actions_keyboard(uid, user.get("is_banned") == 1)
    )

# User Ban / Unban Callback
@router.callback_query(F.data.startswith("uact:ban:") | F.data.startswith("uact:unban:"))
async def cb_user_ban_toggle(call: CallbackQuery):
    if not await db.is_user_admin(call.from_user.id):
        return

    action, uid_str = call.data.split(":")[1], call.data.split(":")[2]
    user_id = int(uid_str)
    new_status = 1 if action == "ban" else 0

    await db.set_user_ban(user_id, new_status)
    await call.answer("Foydalanuvchi holati yangilandi!")

    user = await db.get_user(user_id)
    if user:
        status_str = "🚫 Bloklangan" if user.get("is_banned") == 1 else "✅ Faol"
        uname_str = f"@{user['username']}" if user.get("username") else "Mavjud emas"
        ref_by_str = f"<code>{user['referred_by']}</code>" if user.get("referred_by") else "Hech kim"

        info_text = (
            f"👤 <b>Foydalanuvchi Ma'lumotlari:</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"👤 Ism: <b>{user.get('full_name')}</b>\n"
            f"🔗 Username: {uname_str}\n"
            f"💰 Balans: <b>{user.get('balance', 0.0)} ⭐</b>\n"
            f"👥 Taklif qilgan: <b>{user.get('referrals_count', 0)} ta</b>\n"
            f"🤝 Kim taklif qilgan: {ref_by_str}\n"
            f"💸 Jami yechib olgan: <b>{user.get('total_withdrawn', 0.0)} ⭐</b>\n"
            f"🛡 Holat: <b>{status_str}</b>\n"
            f"📅 Qo'shilgan: <i>{user.get('joined_at')}</i>\n"
            f"⚡ Oxirgi faollik: <i>{user.get('last_active')}</i>"
        )
        try:
            await call.message.edit_text(
                info_text,
                parse_mode="HTML",
                reply_markup=get_user_actions_keyboard(user_id, user.get("is_banned") == 1)
            )
        except Exception:
            pass

# User Balance Callback
@router.callback_query(F.data.startswith("uact:balance:"))
async def cb_user_balance_action(call: CallbackQuery, state: FSMContext):
    if not await db.is_user_admin(call.from_user.id):
        return

    user_id = int(call.data.split(":")[2])
    user = await db.get_user(user_id)
    if not user:
        await call.answer("User topilmadi!", show_alert=True)
        return

    await state.update_data(target_id=user_id)
    await state.set_state(AdminStates.waiting_for_balance_amount)

    await call.message.answer(
        f"💰 <b>{user.get('full_name')} (ID: {user_id})</b> balansi: <b>{user.get('balance', 0.0)} ⭐</b>\n\n"
        f"Qo'shish yoki ayirish miqdorini kiriting (masalan: <code>+50</code> yoki <code>-20</code>):\n\n"
        f"Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(AdminStates.waiting_for_balance_amount)
async def process_user_balance_amount(message: Message, state: FSMContext, bot: Bot):
    if not await db.is_user_admin(message.from_user.id):
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
        delta = -abs(val) if message.text.strip().startswith("-") else abs(val)
    except ValueError:
        await message.answer("⚠️ Noto'g'ri son formati.", reply_markup=get_admin_keyboard())
        return

    ok = await db.update_user_balance(target_id, delta)
    if not ok:
        await message.answer("❌ Foydalanuvchi balansida yetarli mablag' yo'q.", reply_markup=get_admin_keyboard())
        return

    user = await db.get_user(target_id)
    sign = "+" if delta > 0 else ""
    await message.answer(
        f"✅ <b>Balans yangilandi!</b>\n"
        f"ID: <code>{target_id}</code>\n"
        f"O'zgarish: <b>{sign}{delta} ⭐</b>\n"
        f"Yangi balans: <b>{user.get('balance', 0.0)} ⭐</b>",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )

    try:
        await bot.send_message(
            target_id,
            f"ℹ️ <b>Sizning balansingiz admin tomonidan yangilandi:</b>\n"
            f"O'zgarish: <b>{sign}{delta} ⭐</b>\n"
            f"Hozirgi balansingiz: <b>{user.get('balance', 0.0)} ⭐</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass

# Send Direct Message (DM) to User
@router.callback_query(F.data.startswith("uact:dm:"))
async def cb_user_dm_action(call: CallbackQuery, state: FSMContext):
    if not await db.is_user_admin(call.from_user.id):
        return

    user_id = int(call.data.split(":")[2])
    await state.update_data(dm_target_id=user_id)
    await state.set_state(AdminStates.waiting_for_dm_message)

    await call.message.answer(
        f"✉️ <b>ID: {user_id} foydalanuvchiga yubormoqchi bo'lgan xabaringizni yozing:</b>\n\n"
        f"Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(AdminStates.waiting_for_dm_message)
async def process_user_dm_message(message: Message, state: FSMContext, bot: Bot):
    if not await db.is_user_admin(message.from_user.id):
        return

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    data = await state.get_data()
    target_id = data.get("dm_target_id")
    await state.clear()

    try:
        await bot.send_message(
            target_id,
            f"📩 <b>Admin xabari:</b>\n\n{message.html_text}",
            parse_mode="HTML"
        )
        await message.answer(f"✅ Xabar <code>{target_id}</code> ga muvaffaqiyatli yetkazildi!", parse_mode="HTML", reply_markup=get_admin_keyboard())
    except Exception as e:
        await message.answer(f"❌ Xabarni yetkazib bo'lmadi: {e}", reply_markup=get_admin_keyboard())

# ==================== 👑 ADMINLAR BOSHQARUVI ====================
@router.message(F.text == "👑 Adminlar")
async def msg_admin_list(message: Message):
    if not await db.is_user_admin(message.from_user.id):
        return

    admins = await db.get_all_admins()
    user_id = message.from_user.id

    text = (
        "👑 <b>Bot Adminlari Ro'yxati:</b>\n\n"
        f"👑 <b>Bosh Ega (Asosiy Egasi):</b>\n"
        f"• ID: <code>{BOT_OWNER_ID}</code> (Cheksiz vakolatlar: istalgan adminni chiqarib yuborish va huquqlarini o'zgartirish huquqiga ega)\n\n"
        "👤 <b>Boshqa Adminlar:</b>\n"
    )

    count = 1
    for adm in admins:
        uid = adm["user_id"]
        if uid == BOT_OWNER_ID:
            continue
        name = adm.get("full_name") or f"Admin {uid}"
        uname = f"@{adm['username']}" if adm.get("username") else "Yo'q"

        text += (
            f"<b>{count}. {name}</b> ({uname})\n"
            f"   🆔 ID: <code>{uid}</code>\n"
            f"   ⏰ Qo'shilgan: <i>{adm.get('added_at')}</i>\n\n"
        )
        count += 1

    if count == 1:
        text += "<i>Hozircha boshqa adminlar yo'q.</i>\n"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_admins_mgmt_keyboard(admins, current_user_id=user_id)
    )

# Add Admin Callback & Flow
@router.callback_query(F.data == "add_admin")
async def cb_add_admin_prompt(call: CallbackQuery, state: FSMContext):
    if not await db.is_user_admin(call.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_new_admin_id)
    await call.message.answer(
        "👑 <b>Yangi Admin qo'shish:</b>\n\n"
        "Admin qilmoqchi bo'lgan shaxsning <b>Telegram ID</b> raqamini yuboring:\n\n"
        "Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(AdminStates.waiting_for_new_admin_id)
async def process_new_admin_id(message: Message, state: FSMContext, bot: Bot):
    if not await db.is_user_admin(message.from_user.id):
        return

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamdan iborat Telegram ID kiriting.")
        return

    new_admin_id = int(text)
    success = await db.add_admin(new_admin_id, added_by=message.from_user.id)
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>Foydalanuvchi (ID: <code>{new_admin_id}</code>) admin etib tayinlandi!</b>",
            parse_mode="HTML",
            reply_markup=get_admin_keyboard()
        )
        try:
            await bot.send_message(
                new_admin_id,
                "🎉 <b>Siz Pro Stars Botida admin etib tayinlandingiz!</b>\n"
                "Admin panelga kirish uchun /admin buyrug'idan foydalanishingiz mumkin.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        await message.answer("❌ Bu foydalanuvchi allaqachon admin yoki xatolik yuz berdi.", reply_markup=get_admin_keyboard())

# Delete Admin Callback
@router.callback_query(F.data.startswith("deladmin:"))
async def cb_delete_admin(call: CallbackQuery, bot: Bot):
    caller_id = call.from_user.id
    if caller_id != BOT_OWNER_ID:
        await call.answer("❌ Faqat Bosh Ega (618430308) adminlarni chiqarib yubora oladi!", show_alert=True)
        return

    admin_to_del = int(call.data.split(":")[1])
    if admin_to_del == BOT_OWNER_ID:
        await call.answer("❌ Bosh Egani o'chirish mumkin emas!", show_alert=True)
        return

    ok = await db.remove_admin(admin_to_del)
    if ok:
        await call.answer("✅ Admin muvaffaqiyatli chiqarib yuborildi va huquqlari bekor qilindi!", show_alert=True)
        try:
            await bot.send_message(
                admin_to_del,
                "⚠️ <b>Sizning Pro Stars Botidagi adminlik huquqingiz Bosh Ega tomonidan bekor qilindi.</b>",
                parse_mode="HTML"
            )
        except Exception:
            pass

        admins = await db.get_all_admins()
        try:
            await call.message.edit_reply_markup(
                reply_markup=get_admins_mgmt_keyboard(admins, current_user_id=caller_id)
            )
        except Exception:
            pass
    else:
        await call.answer("Xatolik yuz berdi!", show_alert=True)

# ==================== 📥 SO'ROVLAR (BUYURTMALAR) ====================
@router.message(F.text == "📥 So'rovlar")
async def msg_admin_pending_orders(message: Message, bot: Bot):
    if not await db.is_user_admin(message.from_user.id):
        return

    orders = await db.get_pending_orders(limit=10)
    if not orders:
        await message.answer("✅ Hozirda yangi kutilayotgan so'rovlar yo'q!")
        return

    await message.answer(f"📥 <b>Kutilayotgan so'rovlar soni: {len(orders)} ta:</b>", parse_mode="HTML")

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

# Approve Order Callback
@router.callback_query(F.data.startswith("order:approve:"))
async def cb_approve_order(call: CallbackQuery, bot: Bot):
    if not await db.is_user_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan!", show_alert=True)
        return

    order_id = int(call.data.split(":")[2])
    order = await db.get_order(order_id)
    if not order or order["status"] != "pending":
        await call.answer("Buyurtma allaqachon ko'rib chiqilgan!", show_alert=True)
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

        try:
            await bot.send_message(
                order["user_id"],
                f"🎉 <b>Buyurtmangiz tasdiqlandi!</b>\n\n"
                f"🆔 Buyurtma: <b>#{order_id}</b>\n"
                f"⭐ Miqdor: <b>{amt} ⭐</b>\n"
                f"🎯 Manzil: <code>{order['target_account']}</code>\n\n"
                f"Stars hisobingizga muvaffaqiyatli yetkazildi!",
                parse_mode="HTML"
            )
        except Exception:
            pass

        await call.answer("✅ Buyurtma tasdiqlandi!")

# Reject Order Callback & Reason
@router.callback_query(F.data.startswith("order:reject:"))
async def cb_reject_order(call: CallbackQuery, state: FSMContext):
    if not await db.is_user_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan!", show_alert=True)
        return

    order_id = int(call.data.split(":")[2])
    order = await db.get_order(order_id)
    if not order or order["status"] != "pending":
        await call.answer("Buyurtma topilmadi yoki allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await state.update_data(reject_order_id=order_id)
    await state.set_state(AdminStates.waiting_for_reject_reason)

    await call.message.answer(
        f"⚠️ <b>#{order_id} raqamli so'rovni rad etish sababini yozing:</b>\n"
        f"<i>({order['amount']} ⭐ foydalanuvchi hisobiga qaytariladi).</i>\n\n"
        f"Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(AdminStates.waiting_for_reject_reason)
async def process_reject_reason(message: Message, state: FSMContext, bot: Bot):
    if not await db.is_user_admin(message.from_user.id):
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
        amt = int(order["amount"]) if float(order["amount"]).is_integer() else order["amount"]
        await message.answer(
            f"❌ <b>Buyurtma #{order_id} rad etildi.</b>\n"
            f"Sabab: <i>{reason}</i>\n"
            f"⭐ {amt} Stars foydalanuvchi hisobiga qaytarildi.",
            parse_mode="HTML",
            reply_markup=get_admin_keyboard()
        )

        try:
            await bot.send_message(
                order["user_id"],
                f"❌ <b>Sizning Stars yechish so'rovingiz rad etildi.</b>\n\n"
                f"🆔 Buyurtma: <b>#{order_id}</b>\n"
                f"⭐ Miqdor: <b>{amt} ⭐</b>\n"
                f"⚠️ Sabab: <i>{reason}</i>\n\n"
                f"Stars balansingizga qaytarildi.",
                parse_mode="HTML"
            )
        except Exception:
            pass

# ==================== 💰 REFERAL NARXI ====================
@router.message(F.text == "💰 Referal narxi")
async def msg_admin_change_ref(message: Message, state: FSMContext):
    if not await db.is_user_admin(message.from_user.id):
        return

    current = await db.get_setting("ref_bonus", "2")
    await state.set_state(AdminStates.waiting_for_ref_bonus)
    await message.answer(
        f"💰 <b>Hozirda har 1 do'st uchun: {current} ⭐ beriladi.</b>\n\n"
        f"Yangi miqdorni kiriting (masalan: <code>1</code>, <code>2</code>, <code>5</code>, <code>10</code>):\n\n"
        f"Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

@router.message(AdminStates.waiting_for_ref_bonus)
async def process_ref_bonus(message: Message, state: FSMContext):
    if not await db.is_user_admin(message.from_user.id):
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
        await message.answer("⚠️ Iltimos, 0 dan katta to'g'ri son kiriting.")
        return

    val_str = str(int(new_val)) if new_val.is_integer() else str(new_val)
    await db.set_setting("ref_bonus", val_str)
    await state.clear()

    await message.answer(
        f"✅ <b>Muvaffaqiyatli saqlandi!</b>\nEndi har bir taklif qilingan do'st uchun <b>{val_str} ⭐</b> beriladi.",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )

# ==================== 📢 KANALLAR ====================
@router.message(F.text == "📢 Kanallar")
async def msg_admin_channels(message: Message):
    if not await db.is_user_admin(message.from_user.id):
        return

    channels = await db.get_channels()
    text = (
        "📢 <b>Majburiy a'zolik kanallari:</b>\n\n"
        f"Jami kanallar: <b>{len(channels)} ta</b>\n"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_channels_keyboard(channels))

@router.callback_query(F.data == "add_channel")
async def cb_add_channel(call: CallbackQuery, state: FSMContext):
    if not await db.is_user_admin(call.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_channel)
    await call.message.answer(
        "📢 <b>Yangi kanal qo'shish:</b>\n\n"
        "Kanal usernomini yoki havolasini yuboring:\n"
        "• Masalan: <code>@stars_uz</code> yoki <code>https://t.me/stars_uz</code>\n\n"
        "<i>Agar kanal yopiq (privat) bo'lsa:</i>\n"
        "<code>-1001234567890 https://t.me/+havola Kanal Nomi</code>\n\n"
        "⚠️ <b>Muhim:</b> Botni ushbu kanalga <b>Admin</b> qilib qo'yishingiz kerak!\n\n"
        "Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.message(AdminStates.waiting_for_channel)
async def process_add_channel(message: Message, state: FSMContext, bot: Bot):
    if not await db.is_user_admin(message.from_user.id):
        return

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    raw_text = message.text.strip()
    channel_id = ""
    invite_link = ""
    title = ""

    # Check if multiple parts provided (private channel format)
    parts = raw_text.split(maxsplit=2)
    if len(parts) >= 2 and (parts[0].startswith("-100") or parts[0].startswith("-")):
        channel_id = parts[0].strip()
        invite_link = parts[1].strip()
        title = parts[2].strip() if len(parts) > 2 else "Kanal"
    else:
        # Public channel username or link
        clean_user = raw_text.replace("https://t.me/", "").replace("http://t.me/", "").replace("@", "").strip().split("/")[0]
        if not clean_user:
            await message.answer("⚠️ Kanal usernomini to'g'ri kiriting (masalan: @kanal yoki https://t.me/kanal).")
            return
        channel_id = f"@{clean_user}"
        invite_link = f"https://t.me/{clean_user}"
        title = clean_user

    # Test connection to channel via Telegram Bot API
    try:
        chat = await bot.get_chat(channel_id)
        if chat.title:
            title = chat.title
    except Exception as e:
        await message.answer(
            f"❌ <b>Bot ushbu kanalga ulanolmadi!</b>\n\n"
            f"Sabab: <i>{e}</i>\n\n"
            f"⚠️ <b>Iltimos, avval botni ushbu kanalga Admin qilib qo'shing</b>, so'ngra qaytadan urinib ko'ring.",
            parse_mode="HTML"
        )
        return

    # Check if bot has admin rights
    bot_info = await bot.get_me()
    try:
        bot_member = await bot.get_chat_member(chat_id=channel_id, user_id=bot_info.id)
        if bot_member.status not in ("administrator", "creator"):
            await message.answer(
                f"⚠️ <b>Diqqat:</b> Bot «<b>{title}</b>» kanaliga admin qilinmagan!\n"
                f"A'zolikni to'liq tekshira olishi uchun botga kanalda admin huquqini bering.",
                parse_mode="HTML"
            )
    except Exception:
        pass

    success = await db.add_channel(channel_id, title, invite_link)
    await state.clear()

    if success:
        await message.answer(
            f"✅ <b>Kanal muvaffaqiyatli qo'shildi!</b>\n\n"
            f"📢 Nomi: <b>{title}</b>\n"
            f"🆔 ID: <code>{channel_id}</code>\n"
            f"🔗 Havola: {invite_link}\n\n"
            f"🔒 Endi foydalanuvchilar ushbu kanalga a'zo bo'lmaguncha botdan foydalana olishmaydi!",
            parse_mode="HTML",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer("❌ Kanal qo'shishda xatolik yuz berdi.", reply_markup=get_admin_keyboard())

@router.callback_query(F.data.startswith("delchan:"))
async def cb_delete_channel(call: CallbackQuery):
    if not await db.is_user_admin(call.from_user.id):
        return

    channel_id = call.data.split("delchan:")[1]
    await db.delete_channel(channel_id)
    await call.answer(f"{channel_id} o'chirildi!")

    channels = await db.get_channels()
    try:
        await call.message.edit_reply_markup(reply_markup=get_admin_channels_keyboard(channels))
    except Exception:
        pass

# ==================== ✉️ XABAR YUBORISH (BROADCAST) ====================
@router.message(F.text == "✉️ Xabar yuborish")
async def msg_admin_broadcast(message: Message, state: FSMContext):
    if not await db.is_user_admin(message.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_broadcast)
    await message.answer(
        "✉️ <b>Barcha bot foydalanuvchilariga xabar yuborish:</b>\n\n"
        "<i>(Matn, rasm, video, audio yuborishingiz mumkin)</i>\n\n"
        "Bekor qilish uchun «❌ Bekor qilish» deb yozing.",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

@router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not await db.is_user_admin(message.from_user.id):
        return

    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    await state.clear()
    status_msg = await message.answer("⏳ Xabar tarqatish boshlandi...")

    user_ids = await db.get_all_user_ids(only_active=True)
    total = len(user_ids)
    success = 0
    failed = 0

    for uid in user_ids:
        try:
            await message.copy_to(chat_id=uid)
            success += 1
            await asyncio.sleep(0.04)  # Rate limit protection
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"👥 Jami qabul qiluvchilar: <b>{total} ta</b>\n"
        f"✅ Yetib bordi: <b>{success} ta</b>\n"
        f"❌ Yetib bormadi (bloklaganlar): <b>{failed} ta</b>",
        parse_mode="HTML"
    )


# ==================== 🎟 PROMOKODLAR BOSHQARUVI ====================

@router.message(F.text == "🎟 Promokodlar")
async def msg_admin_promocodes(message: Message, state: FSMContext):
    if not await db.is_user_admin(message.from_user.id):
        return

    await state.clear()
    promocodes = await db.get_all_promocodes()
    active_count = sum(1 for p in promocodes if p["is_active"] and p["uses_count"] < p["max_uses"])

    text = (
        f"🎟 <b>Promokodlar Boshqaruvi</b>\n\n"
        f"Jami promokodlar: <b>{len(promocodes)} ta</b> (Faol: <b>{active_count} ta</b>)\n\n"
        f"<i>Eslatma: Yaratilgan promokod kanallarga avtomatik yuborilmaydi. "
        f"Bot sizga kanalingizga tashlash uchun chiroyli tayyor xabar taqdim etadi — "
        f"uni o'zingiz nusxalab, xohlagan kanalingizga tashlaysiz!</i>"
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_promocodes_mgmt_keyboard(promocodes)
    )

@router.callback_query(F.data == "add_promocode")
async def cb_add_promocode(call: CallbackQuery, state: FSMContext):
    if not await db.is_user_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan!", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_promo_code)
    await call.message.answer(
        "🎟 <b>1-qadam: Promokod nomini kiriting:</b>\n\n"
        "Masalan: <code>YULDUZ10</code>, <code>START2026</code> yoki istalgan so'z.\n"
        "<i>(Yoki pastdagi tugmani bosib tasodifiy avto-kod generatsiya qiling)</i>",
        parse_mode="HTML",
        reply_markup=get_promo_auto_keyboard()
    )
    await call.answer()

@router.callback_query(F.data == "promo:autocode")
async def cb_promo_autocode(call: CallbackQuery, state: FSMContext):
    if not await db.is_user_admin(call.from_user.id):
        return

    rand_suffix = "".join(random.choices(string.digits, k=4))
    auto_code = f"STARS{rand_suffix}"
    await state.update_data(promo_code=auto_code)
    await state.set_state(AdminStates.waiting_for_promo_reward)

    await call.message.answer(
        f"🔑 Tanlangan kod: <code>{auto_code}</code>\n\n"
        f"⭐ <b>2-qadam: Har bir foydalanuvchiga qancha Stars berilsin?</b>\n\n"
        f"Masalan: <code>1</code>, <code>2</code>, <code>5</code>, <code>10</code>...\n"
        f"<i>(Bekor qilish uchun «❌ Bekor qilish» deb yozing)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()

@router.callback_query(F.data == "promo:cancel")
async def cb_promo_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    promocodes = await db.get_all_promocodes()
    try:
        await call.message.edit_text(
            "🎟 <b>Promokodlar ro'yxati:</b>",
            parse_mode="HTML",
            reply_markup=get_promocodes_mgmt_keyboard(promocodes)
        )
    except Exception:
        pass
    await call.answer("Bekor qilindi.")

@router.message(AdminStates.waiting_for_promo_code)
async def process_promo_code_input(message: Message, state: FSMContext):
    if not await db.is_user_admin(message.from_user.id):
        return

    text = message.text.strip()
    if text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    code = text.upper()
    if len(code) < 3 or len(code) > 30:
        await message.answer("⚠️ Promokod uzunligi 3 tadan 30 tagacha belgidan iborat bo'lishi kerak. Qaytadan kiriting:")
        return

    existing = await db.get_promocode(code)
    if existing:
        await message.answer(f"⚠️ <code>{code}</code> nomli promokod allaqachon mavjud! Iltimos, boshqa nom tanlang:", parse_mode="HTML")
        return

    await state.update_data(promo_code=code)
    await state.set_state(AdminStates.waiting_for_promo_reward)
    await message.answer(
        f"🔑 Promokod: <code>{code}</code>\n\n"
        f"⭐ <b>2-qadam: Har bir foydalanuvchiga qancha Stars berilsin?</b>\n\n"
        f"Masalan: <code>1</code>, <code>2</code>, <code>5</code>, <code>10</code>...\n"
        f"<i>(Bekor qilish uchun «❌ Bekor qilish» deb yozing)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

@router.message(AdminStates.waiting_for_promo_reward)
async def process_promo_reward_input(message: Message, state: FSMContext):
    if not await db.is_user_admin(message.from_user.id):
        return

    text = message.text.strip()
    if text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    try:
        reward = float(text.replace(",", "."))
        if reward <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Iltimos, noldan katta musbat son kiriting (masalan: 2 yoki 5):")
        return

    await state.update_data(promo_reward=reward)
    await state.set_state(AdminStates.waiting_for_promo_limit)

    display_reward = int(reward) if reward.is_integer() else reward
    await message.answer(
        f"⭐ Mukofot: <b>{display_reward} ⭐</b>\n\n"
        f"👥 <b>3-qadam: Ushbu promokodni jami nechta odam ishlata olsin? (Limit)</b>\n\n"
        f"Masalan: <code>10</code>, <code>50</code>, <code>100</code> ta foydalanuvchi.\n"
        f"<i>(Bekor qilish uchun «❌ Bekor qilish» deb yozing)</i>",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )

@router.message(AdminStates.waiting_for_promo_limit)
async def process_promo_limit_input(message: Message, state: FSMContext, bot: Bot):
    if not await db.is_user_admin(message.from_user.id):
        return

    text = message.text.strip()
    if text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    if not text.isdigit() or int(text) <= 0:
        await message.answer("⚠️ Iltimos, limit sonini butun musbat son ko'rinishida kiriting (masalan: 20 yoki 50):")
        return

    limit = int(text)
    data = await state.get_data()
    code = data["promo_code"]
    reward = data["promo_reward"]
    await state.clear()

    created = await db.create_promocode(code, reward, limit)
    if not created:
        await message.answer("❌ Promokodni saqlashda xatolik yuz berdi. Balki bu kod allaqachon mavjuddir.", reply_markup=get_admin_keyboard())
        return

    bot_info = await bot.get_me()
    bot_username = bot_info.username
    display_reward = int(reward) if reward.is_integer() else reward

    admin_report = (
        f"✅ <b>Promokod muvaffaqiyatli yaratildi!</b>\n\n"
        f"🔑 Kod: <code>{code}</code>\n"
        f"⭐ Mukofot: <b>{display_reward} ⭐</b>\n"
        f"👥 Limit: <b>{limit} ta odam</b>\n\n"
        f"📢 <b>Kanalingizga tashlash uchun tayyor post:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 <b>TEZKOR PROMOKOD!</b>\n\n"
        f"Botimiz foydalanuvchilari uchun maxsus promokod!\n"
        f"Birinchi bo'lib kiring va bepul Stars oling!\n\n"
        f"🔑 Promokod: <code>{code}</code>\n"
        f"⭐ Mukofot: <b>{display_reward} ⭐ Stars</b>\n"
        f"👥 Limit: Dastlabki <b>{limit}</b> ta foydalanuvchi uchun!\n\n"
        f"👇 Botga kirib <b>«🎟 Promokod»</b> bo'limiga yozing:\n"
        f"👉 @{bot_username}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>(Ushbu xabarni nusxalab kanalingizga yuborishingiz mumkin)</i>"
    )

    await message.answer(admin_report, parse_mode="HTML", reply_markup=get_admin_keyboard())

@router.callback_query(F.data.startswith("delpromo:"))
async def cb_delete_promocode(call: CallbackQuery):
    if not await db.is_user_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan!", show_alert=True)
        return

    code = call.data.split(":")[1]
    await db.delete_promocode(code)
    await call.answer(f"🗑 {code} o'chirildi!", show_alert=True)

    promocodes = await db.get_all_promocodes()
    try:
        await call.message.edit_reply_markup(
            reply_markup=get_promocodes_mgmt_keyboard(promocodes)
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("promoinfo:"))
async def cb_promocode_info(call: CallbackQuery):
    if not await db.is_user_admin(call.from_user.id):
        return

    code = call.data.split(":")[1]
    promo = await db.get_promocode(code)
    if not promo:
        await call.answer("Promokod topilmadi!", show_alert=True)
        return

    reward = int(promo["reward"]) if float(promo["reward"]).is_integer() else promo["reward"]
    status_str = "🟢 Faol" if (promo["is_active"] and promo["uses_count"] < promo["max_uses"]) else "🔴 Limit tugagan / Nofaol"

    info_text = (
        f"🎟 <b>Promokod:</b> <code>{promo['code']}</code>\n"
        f"⭐ <b>Mukofot:</b> {reward} ⭐\n"
        f"👥 <b>Foydalanildi:</b> {promo['uses_count']} / {promo['max_uses']} ta\n"
        f"📊 <b>Holati:</b> {status_str}\n"
        f"📅 <b>Yaratilgan:</b> {promo['created_at']}"
    )
    await call.answer(f"{promo['code']}: {promo['uses_count']}/{promo['max_uses']} ishlatilgan", show_alert=True)
