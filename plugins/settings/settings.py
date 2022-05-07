import os
import time
import random
import logging
import asyncio

from pyrogram.emoji import *
from pyrogram.errors import FloodWait
from pyrogram.types import ForceReply
from pyrogram.enums import MessageEntityType, ParseMode
from pyrogram import Client, types, errors, filters

from dotenv import load_dotenv
from database.users_chats_db import db
from info import START_BUTTONS, LOGIN_BUTTON, START_TXT, PASS, PICS


if os.path.exists('config.env'):
    load_dotenv('config.env')

logger = logging.getLogger(__name__)


async def Settings(m: "types.Message"):
    user_id = m.chat.id

    if m.entities:
        if m.entities[0].type is MessageEntityType.BOT_COMMAND:
            message = await m.reply_text('**İşleniyor..**', reply_to_message_id=m.id)
            message = message.edit
    else:
        message = m.edit

    user_data = await db.get_user_data(user_id)

    if not user_data:
        await message("Verileriniz veritabanından alınamadı!")
        return

    get_notif = user_data.get("notif", False)

    buttons_markup = [
        [
            types.InlineKeyboardButton(f"{'🔔' if get_notif else '🔕'} Bildirimler",
                                       callback_data="notifon")],
        [
            types.InlineKeyboardButton(f"🔙 Geri",
                                       callback_data="start"),
            types.InlineKeyboardButton(f"Kapat",
                                       callback_data='close_data')]
    ]

    try:
        await message(
            text="**⚙ Bot Ayarları**",
            reply_markup=types.InlineKeyboardMarkup(buttons_markup),
            disable_web_page_preview=True
        )
    except errors.MessageNotModified:
        pass
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as err:
        logger.error(err)


async def Login(c, m: "types.Message"):
    chat_id = m.chat.id
    if PASS:
        try:
            logged = await db.get_user_pass(chat_id)
            if logged != PASS:
                await db.delete_user(chat_id)
            elif logged:
                return await m.reply(f"__Zaten giriş yaptınız.__ {VICTORY_HAND}")
            try:
                msg = await m.reply(
                    "**Şimdi bana şifre gönder.**\n\n__(İşlemi iptal etmek için /iptal komutunu kullanabilirsiniz.)__",
                    reply_markup=ForceReply(True))
                _text = await c.listen(m.chat.id, filters=filters.text, timeout=90)
                if _text.text:
                    textp = _text.text
                    if textp == "/iptal":
                        await m.delete(True)
                        await msg.delete(True)
                        await msg.reply("__İşlem Başarıyla İptal Edildi.__")
                        return
                else:
                    return
            except TimeoutError:
                await m.reply("__Şifre için daha fazla bekleyemem, tekrar dene.__")
                return
            if textp == PASS:
                await db.add_user_pass(chat_id, m.from_user.first_name, textp)
                msg_text = f"__Evet! Başarıyla Oturum Açıldı.\nKeyfini çıkarın.__ {FACE_SAVORING_FOOD}"
                buttons = START_BUTTONS
                reply_markup = buttons
                await c.send_photo(
                    chat_id=chat_id,
                    photo=random.choice(PICS),
                    caption=START_TXT.format(m.from_user.mention),
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=True
                )
            else:
                msg_text = "__Yanlış şifre, tekrar deneyin. /login__"
            await m.reply(msg_text)
        except FloodWait as e:
            time.sleep(e.value)
        except Exception as e:
            logging.error(e)
        await m.delete(True)
        await msg.delete(True)

@Client.on_callback_query()
async def cb_handler(client, cb: "types.CallbackQuery"):
    user_id = cb.from_user.id
    message = cb.message
    if cb.data == "close_data":
        await message.delete()
    elif cb.data == "start":
        await cb.answer()
        reply_markup = START_BUTTONS
        await message.edit_text(
            text=START_TXT.format(cb.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    elif cb.data == "notifon":
        notif = await db.get_notif(user_id)
        if notif:
            await cb.answer("Bot bildirimleri kapatıldı.", True)
            await db.set_notif(user_id, False)
        else:
            await cb.answer("Bot bildirimleri etkinleştirildi.", True)
            await db.set_notif(user_id, True)
        await Settings(message)
    elif cb.data == "settings":
        await cb.answer()
        await Settings(message)
    elif cb.data == "login🔑":
        await cb.answer()
        await Login(client, message)
