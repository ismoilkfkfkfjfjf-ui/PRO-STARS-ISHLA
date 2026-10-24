from aiogram import Bot
from aiogram.enums import ChatMemberStatus
import database as db
import logging

async def check_user_subscription(bot: Bot, user_id: int) -> tuple[bool, list[dict]]:
    """
    Checks if user is subscribed to all mandatory channels.
    Returns (is_all_subscribed, unjoined_channels_list)
    """
    channels = await db.get_channels()
    if not channels:
        return True, []

    unjoined = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["channel_id"], user_id=user_id)
            if member.status not in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR,
                ChatMemberStatus.RESTRICTED
            ):
                unjoined.append(ch)
        except Exception as e:
            logging.warning(f"Could not check subscription for {ch['channel_id']}: {e}")
            # If bot can't check (e.g. not admin in channel), we don't block the user
            pass

    return (len(unjoined) == 0), unjoined
