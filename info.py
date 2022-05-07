import os
import re
import time
from os import environ
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

if os.path.exists('config.env'):
    load_dotenv('config.env')

id_pattern = re.compile(r'^.\d+$')

# Bot information
SESSION = environ.get('SESSION', 'Media_search')
API_ID = int(environ['API_ID'])
API_HASH = environ['API_HASH']
BOT_TOKEN = environ['BOT_TOKEN']

# Bot settings
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', True))
PICS = (environ.get('PICS',
                    'https://telegra.ph/file/7e56d907542396289fee4.jpg https://telegra.ph/file/9aa8dd372f4739fe02d85.jpg https://telegra.ph/file/adffc5ce502f5578e2806.jpg')).split()

# Admins, Channels & Users
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '').split()]
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '0').split()]
auth_users = [int(user) if id_pattern.search(user) else user for user in environ.get('AUTH_USERS', '').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []
auth_channel = environ.get('AUTH_CHANNEL')
auth_grp = environ.get('AUTH_GROUP')
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
AUTH_GROUPS = [int(ch) for ch in auth_grp.split()] if auth_grp else None

# MongoDB information
DATABASE_URI = environ.get('DATABASE_URI', "")
DATABASE_NAME = environ.get('DATABASE_NAME', "dzflm")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Telegram_files')

# Messages
default_start_msg = """
<b>Hi, {},</b>
Here you can search files in inline mode. Just press following buttons and start searching.
"""
default_share_button_msg = """
Checkout {username} for searching files
"""
default_status_msg = """
★ Toplam dosya: <code>{}</code>
★ Topladım kullanıcı: <code>{}</code>
★ Kullanılmış depolama: <code>{}</code> 𝙼𝚒𝙱
★ Ücretsiz depolama: <code>{}</code> 𝙼𝚒𝙱
"""
default_log_msg = """
#YeniKullanıcı

ID - <code>{}</code>
Adı - {}
Dil - {}
Kullanıcı Adı - {}
DC - {}
Bot - @{}
"""
default_forcesub_msg = """
**Sadece kanal aboneleri kullanabilir.**
(__Katıldıktan sonra tekrar deneyin.__)
"""
default_login_msg = """
**Öncelikle butona basarak giriş yapınız.**

__(Şifreyi bilmiyor musunuz?\n@korsanistekbot'tan isteyin.)__
"""
LOGIN_TXT = environ.get('LOGIN_TXT', default_login_msg)
START_TXT = environ.get('START_TXT', default_start_msg)
FORCE_TXT = environ.get('FORCE_TXT', default_forcesub_msg)
SHARE_BUTTON_TEXT = environ.get('SHARE_BUTTON_TEXT', default_share_button_msg)
BUTTON_TEXT = "🤖 Kanala Katıl"
STATUS_TXT = environ.get('STATUS_TXT', default_status_msg)
LOG_TEXT_P = environ.get('LOG_TEXT_P', default_log_msg)

# Others
log_channel = environ.get('LOG_CHANNEL')
LOG_CHANNEL = int(log_channel) if log_channel else None
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", None)
BROADCAST_AS_COPY = bool(environ.get("BROADCAST_AS_COPY", True))
SEND_LOGS_WHEN_DYING = str(environ.get("SEND_LOGS_WHEN_DYING", "True")).lower() == 'true'
BOT_PASSWORD = environ.get("BOT_PASSWORD", "") if environ.get("BOT_PASSWORD", "") else None

# Heroku
HEROKU_APP_NAME = environ.get('HEROKU_APP_NAME', None)
HEROKU_API_KEY = environ.get('HEROKU_API_KEY', None)

# Pasaport
PASS = os.environ.get("PASS",None)

START_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('🔍 Ara', switch_inline_query_current_chat='')
    ],
    [
        InlineKeyboardButton('⚙ Ayarlar', callback_data='settings')
    ]
])

LOGIN_BUTTON = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Oturum Aç 🔐', callback_data='login🔑')
    ]
])

botStartTime = time.time()