from database.users_chats_db import db
from pyrogram import Client
from pyrogram.types import Message
from info import LOG_CHANNEL, LOG_TEXT_P

import logging

logger = logging.getLogger(__name__)


async def add_user_to_database(c: Client, cmd: Message):
    bot = await c.get_me()
    BOT_USERNAME = bot.username
    user = cmd.from_user
    dc_id = user.dc_id or "[Kullanıcının Geçerli Bir DC'si Yok]"
    username = user.username or "Yok"
    if not await db.is_user_exist(user.id):
        if LOG_CHANNEL:
            await c.send_message(LOG_CHANNEL,
                                 LOG_TEXT_P.format(user.id,
                                                   user.mention,
                                                   user.language_code,
                                                   username,
                                                   dc_id,
                                                   BOT_USERNAME
                                                   ))
        else:
            logging.info(f"#YeniKullanıcı :- Ad : {user.first_name} ID : {user.id}")
        await db.add_user(user.id, user.first_name)
