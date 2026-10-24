from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
import database as db
import logging

async def check_user_subscription(bot: Bot, user_id: int) -> tuple[bool, list[dict]]:
    """
    Checks if user is subscribed to all mandatory channels in DB.
    Returns (is_all_subscribed: bool, unjoined_channels_list: list[dict])
    """
    channels = await db.get_channels()
    if not channels:
        return True, []

    unjoined = []
    for ch in channels:
        raw_id = str(ch["channel_id"]).strip()
        chat_id = int(raw_id) if (raw_id.startswith("-") and raw_id[1:].isdigit()) or raw_id.isdigit() else raw_id

        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                unjoined.append(ch)
            elif member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
                # Subscribed!
                pass
            elif member.status == ChatMemberStatus.RESTRICTED:
                # If restricted, check if is_member
                if not getattr(member, 'is_member', True):
                    unjoined.append(ch)
        except TelegramBadRequest as e:
            err_msg = str(e).lower()
            # If Telegram says "user not found" or "participant_id_invalid", user has never joined
            if "user not found" in err_msg or "participant" in err_msg or "chat not found" in err_msg:
                unjoined.append(ch)
            else:
                logging.warning(f"TelegramBadRequest for channel {raw_id}: {e}")
                # Don't penalize user if bot itself lacks permission
        except Exception as e:
            logging.warning(f"Error checking sub for {raw_id}: {e}")

    return (len(unjoined) == 0), unjoined
