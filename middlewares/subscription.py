from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from typing import Callable, Dict, Any, Awaitable
from utils.subscription import check_user_subscription
from keyboards.inline import get_sub_channels_keyboard
import database as db

class MandatorySubMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        bot = data["bot"]
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        user_id = user.id

        # Skip check for admins
        if await db.is_user_admin(user_id):
            return await handler(event, data)

        # Allow /start command to pass through (it has its own deep link referral logic)
        if isinstance(event, Message):
            if event.text and event.text.startswith("/start"):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            if event.data == "check_subscription":
                return await handler(event, data)

        # Check subscription for all other messages and callbacks
        is_subbed, unjoined = await check_user_subscription(bot, user_id)
        if not is_subbed:
            kb = get_sub_channels_keyboard(unjoined)
            text = (
                "⚠️ <b>Botdan to'liq foydalanish uchun quyidagi rasmiy kanallarga a'zo bo'ling:</b>\n\n"
                "Barcha kanallarga a'zo bo'lgach, <b>«✅ Tekshirish»</b> tugmasini bosing."
            )
            if isinstance(event, Message):
                await event.answer(text, parse_mode="HTML", reply_markup=kb)
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ Botdan foydalanish uchun kanallarga a'zo bo'ling!", show_alert=True)
                try:
                    await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
                except Exception:
                    pass
            return

        return await handler(event, data)
