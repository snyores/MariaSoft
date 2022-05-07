import logging
import logging.config
import time

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

from pyrogram import Client, __version__
from pyromod import listen
from pyrogram.raw.all import layer
from functions.utils import ReadableTime, temp
from info import ADMINS, SESSION, API_ID, API_HASH, BOT_TOKEN, SEND_LOGS_WHEN_DYING

botStartTime = time.time()


class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins=dict(root="plugins"),
            sleep_threshold=5,
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        if ADMINS != 0:
            try:
                await self.send_message(text="Karanlığın küllerinden yeniden doğdum.", chat_id=ADMINS[0])
            except Exception as t:
                logging.error(str(t))

    async def stop(self, *args):
        if ADMINS != 0:
            texto = f"Son nefesimi verdim.\nÖldüğümde yaşım: {ReadableTime(time.time() - botStartTime)}"
            try:
                if SEND_LOGS_WHEN_DYING:
                    await self.send_document(document='log.txt', caption=texto, chat_id=ADMINS[0])
                else:
                    await self.send_message(text=texto, chat_id=ADMINS[0])
            except Exception as t:
                logging.error(str(t))
        await super().stop()
        logging.info("Bot durdu. Hoşçakal.")
        exit()


app = Bot()
app.run()
