import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, \
    UsernameNotModified, ChannelPrivate
from pyrogram.enums import MessageMediaType, ChatType
from info import ADMINS, botStartTime
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from functions.utils import temp
import re, time
from functions.utils import ReadableTime
from info import LOG_CHANNEL

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()


@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("İndeksleme İptal Ediliyor")
    _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    if raju == 'reject':
        await query.message.delete()
        await bot.send_message(int(from_user),
                               f'Eklenmesi için gönderdiğiniz dosya moderatörlerimiz tarafından reddedildi.',
                               reply_to_message_id=int(lst_msg_id))
        return

    if lock.locked():
        return await query.answer('Önceki işlem tamamlanana kadar bekleyin.', show_alert=True)
    msg = query.message

    await query.answer('İşleniyor...⏳', show_alert=True)
    if int(from_user) not in ADMINS:
        await bot.send_message(int(from_user),
                               f'Eklenmesi için gönderdiğiniz dosya moderatörlerimiz tarafından kabul edildi ve yakında eklenecek.',
                               reply_to_message_id=int(lst_msg_id))
    await msg.edit(
        "İndeksleme Başlatılıyor",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('İptal Et ✖', callback_data='index_cancel')]]
        )
    )
    try:
        chat = int(chat)
    except:
        chat = chat
    await index_files_to_db(int(lst_msg_id), chat, msg, bot)


@Client.on_message((filters.forwarded | (filters.regex(
    "(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text) & filters.private & filters.incoming)
async def send_for_index(bot, message):
    if message.text:
        regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(message.text)
        if not match:
            return await message.reply('Geçersiz Link')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id = int(("-100" + chat_id))
    elif message.forward_from_chat.type == ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return
    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid or ChannelPrivate:
        return await message.reply(
            'Bu özel bir kanal/grup olabilir.\nDosyaları indekslemek için beni orada yönetici yap.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Geçersiz Bağlantı belirtildi.')
    except Exception as e:
        logger.exception(e)
        return await message.reply(f'Hatalar - {e}')
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except:
        return await message.reply('Kanal gizli ise kanalda yönetici olduğumdan emin olun.')
    if k.empty:
        return await message.reply('Bu grup olabilir ve ben bu grubun yöneticisi değilim.')

    if message.from_user.id in ADMINS:
        buttons = [
            [
                InlineKeyboardButton('Evet ✔',
                                     callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
            ],
            [
                InlineKeyboardButton('İptal Et ✖', callback_data='close_data'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        return await message.reply(
            f'Bu Kanalı/Grubu İndekslemek İstiyormusunuz ?\n\n'
            f'Kanal ID/Username: `{chat_id}`\n'
            f'Son Mesaj ID: `{last_msg_id}`\n'
            f'Başlangıç ID: {str(temp.CURRENT)}',
            reply_markup=reply_markup)

    if type(chat_id) is int:
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply('Sohbette yönetici olduğumdan ve kullanıcıları davet etme iznine sahip olduğumdan emin olun.')
    else:
        link = f"@{message.forward_from_chat.username}"
    buttons = [
        [
            InlineKeyboardButton('İsteği Kabul Et ✔',
                                 callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
        ],
        [
            InlineKeyboardButton('İsteği Reddet ✖',
                                 callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(LOG_CHANNEL,
                           f'#Talep\n\n'
                           f'By : {message.from_user.mention} (`{message.from_user.id}`)\n'
                           f'Kanal ID/Username: `{chat_id}`\n'
                           f'Son Mesaj ID: `{last_msg_id}`\n'
                           f'Link: {link}',
                           reply_markup=reply_markup)
    await message.reply('Katkılarınız İçin Teşekkürler,\nModeratörlerimin dosyaları doğrulamasını bekleyin.')


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except:
            return await message.reply("Skip number should be an integer.")
        await message.reply(f"Successfully set SKIP number as {skip}")
        temp.CURRENT = int(skip)
    else:
        await message.reply("Give me a skip number")


async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    external = 0
    starting = time.time()
    speed = 0
    async with lock:
        try:
            total = lst_msg_id + 1
            current = temp.CURRENT
            temp.CANCEL = False
            while current < total:
                try:
                    message = await bot.get_messages(chat_id=chat, message_ids=current, replies=0)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    message = await bot.get_messages(
                        chat,
                        current,
                        replies=0
                    )
                except Exception as e:
                    logger.exception(e)
                try:
                    speed = (current / ((time.time() - starting).__round__())).__round__()
                except:
                    speed = 0
                if temp.CANCEL:
                    await msg.edit(f"Başarıyla İptal Edildi\n\n"
                                   f"`{total_files}` Dosya başarıyla kaydedildi!\n"
                                   f"Yinelenen Dosyalar Atlandı: `{duplicate}`\n"
                                   f"Silinen Mesajlar Atlandı: `{deleted}`\n"
                                   f"Medya Dışı Mesajlar Atlandı: `{no_media + unsupported}`(Desteklenmeyen Medya - `{unsupported}` )\n"
                                   f"Es geçilenler: `{external}`\n"
                                   f"Oluşan Hatalar: `{errors}`\n"
                                   f"Süre: `{ReadableTime(time.time() - starting)}`\n"
                                   f"Hız: `{speed} öge/saniye`\n"
                                   f"Bot Ömrü: `{ReadableTime(time.time() - botStartTime)}`")
                    break
                current += 1
                if current % 20 == 0:
                    reply = InlineKeyboardMarkup([[InlineKeyboardButton('İptal Et ✖', callback_data='index_cancel')]])
                    try:
                        await msg.edit_text(text=f"Başlangıç ID: {str(temp.CURRENT)}\n"
                                                 f"ileti Sayısı: `{current}`\n"
                                                 f"Kaydedilen Mesajlar: `{total_files}`\n"
                                                 f"Benzer Dosyalar: `{duplicate}`\n"
                                                 f"Silinen Mesajlar: `{deleted}`\n"
                                                 f"Medya Dışı Mesajlar: `{no_media}`\n"
                                                 f"Desteklenmeyen Medyalar: `{unsupported}`\n"
                                                 f"Oluşan Hatalar: `{errors}`\n"
                                                 f"Es Geçilenler: `{external}`\n"
                                                 f"Dizin: `/setskip {current}`\n"
                                                 f"Süre: `{ReadableTime(time.time() - starting)}`\n"
                                                 f"Hız: `{speed} öge/saniye`\n"
                                                 f"Bot Ömrü: `{ReadableTime(time.time() - botStartTime)}`",
                                            reply_markup=reply)
                    except:
                        pass
                if message.empty:
                    deleted += 1
                    continue
                elif not message.media:
                    no_media += 1
                    continue
                elif message.media not in [MessageMediaType.AUDIO, MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
                    unsupported += 1
                    continue
                media = getattr(message, message.media.value, None)
                if not media:
                    unsupported += 1
                    continue
                media.file_type = message.media.value
                media.caption = message.caption
                res = await save_file(media)
                if res == 1:
                    total_files += 1
                elif res == 2:
                    duplicate += 1
                elif res == 3:
                    errors += 1
                elif res == 4:
                    external += 1
        except Exception as e:
            logger.exception(e)
            await msg.edit(f'Hata: {e}')
        else:
            await msg.edit(f'`{total_files}` Dosya başarıyla kaydedildi!\n'
                           f'Benzer Dosyalar: `{duplicate}`\n'
                           f'Silinen Mesajlar: `{deleted}`\n'
                           f'Medya Dışı Mesajlar: `{no_media}`\n'
                           f'Desteklenmeyen Medyalar: `{unsupported}`\n'
                           f'Es Geçilenler: `{external}`\n'
                           f'Oluşan Hatalar: `{errors}`\n'
                           f'Süre: `{ReadableTime(time.time() - starting)}`\n'
                           f'Hız: `{speed} öge/saniye`\n'
                           f'Bot Ömrü: `{ReadableTime(time.time() - botStartTime)}`')
