import datetime

from app import logger
from app.telegram import bot
from telebot.apihelper import ApiTelegramException
from datetime import datetime
from app.telegram.utils.keyboard import BotKeyboard
from app.utils.system import readable_size
from config import TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID
from telebot.formatting import escape_html
from app.models.admin import Admin
from app.models.user import UserDataLimitResetStrategy
from app.gdrive.download import get_file_id_and_download_link
from cli.subscription import get_config, ConfigFormat 

def report(admin_id: int, message: str, parse_mode="html", keyboard=None):
    if bot and (TELEGRAM_ADMIN_ID or TELEGRAM_LOGGER_CHANNEL_ID):
        try:
            if TELEGRAM_LOGGER_CHANNEL_ID:
                bot.send_message(TELEGRAM_LOGGER_CHANNEL_ID, message, parse_mode=parse_mode)
            else:
                for admin in TELEGRAM_ADMIN_ID:
                    bot.send_message(admin, message, parse_mode=parse_mode, reply_markup=keyboard)
            if admin_id:
                bot.send_message(admin_id, message, parse_mode=parse_mode)
        except ApiTelegramException as e:
            logger.error(e)

def report_new_user(user_id: int, username: str, by: str, expire_date: int, data_limit: int, proxies: list, 
                    data_limit_reset_strategy: str, admin: Admin = None):
    try:
        config_format = ConfigFormat.v2ray  # or ConfigFormat.clash depending on your requirement
        output_file = f"/var/lib/marzban/gdrive_mount/Alpha/{by}/{username}.txt"  # If you want to write to a file, specify the file path here
        by=by
        as_base64 = True  # Set to True if you want the output in base64 format
        get_config(username=username, config_format=config_format, output_file=output_file, as_base64=as_base64)
    except Exception:
        pass
    
    text = '''\
🆕 <b>#Created</b>
➖➖➖➖➖➖➖➖➖
<b>Username :</b> <code>{username}</code>
<b>Traffic Limit :</b> <code>{data_limit}</code>
<b>Expire Date :</b> <code>{expire_date}</code>
<b>Proxies :</b> <code>{proxies}</code>
<b>Data Limit Reset Strategy :</b> <code>{data_limit_reset_strategy}</code>
➖➖➖➖➖➖➖➖➖
<b>Belongs To :</b> <code>{belong_to}</code>
<b>By :</b> <b>#{by}</b>
➖➖➖➖➖➖➖➖➖
<b>Subscription link:</b>
<code>{gdrive_download_link}</code>'''.format(
        belong_to=escape_html(admin.username) if admin else None,
        by=escape_html(by),
        username=escape_html(username),
        data_limit=readable_size(data_limit) if data_limit else "Unlimited",
        expire_date=datetime.fromtimestamp(expire_date).strftime("%H:%M:%S %Y-%m-%d") if expire_date else "Never",
        proxies="" if not proxies else ", ".join([escape_html(proxy) for proxy in proxies]),
        data_limit_reset_strategy=escape_html(data_limit_reset_strategy),
        gdrive_download_link=get_file_id_and_download_link(folder_name=escape_html(by), file_name=escape_html(username)),
    )

    return report(
        admin_id=admin.telegram_id if admin and admin.telegram_id else None,
        message=text,
        keyboard=BotKeyboard.user_menu({
            'username': username,
            'id': user_id,
            'status': 'active'
        }, with_back=False)
    )


def report_user_modification(
        username: str,
        expire_date: int,
        data_limit: int,
        proxies: list,
        by: str,
        data_limit_reset_strategy: UserDataLimitResetStrategy,
        admin: Admin = None
):
    text = '''\
✏️ <b>#Modified</b>
➖➖➖➖➖➖➖➖➖
<b>Username :</b> <code>{username}</code>
<b>Traffic Limit :</b> <code>{data_limit}</code>
<b>Expire Date :</b> <code>{expire_date}</code>
<b>Protocols :</b> <code>{protocols}</code>
<b>Data Limit Reset Strategy :</b> <code>{data_limit_reset_strategy}</code>
➖➖➖➖➖➖➖➖➖
<b>Belongs To :</b> <code>{belong_to}</code>
<b>By :</b> <b>#{by}</b>\
    '''.format(
        belong_to=escape_html(admin.username) if admin else None,
        by=escape_html(by),
        username=escape_html(username),
        data_limit=readable_size(data_limit) if data_limit else "Unlimited",
        expire_date=datetime.fromtimestamp(expire_date).strftime("%H:%M:%S %Y-%m-%d") if expire_date else "Never",
        protocols=', '.join([p for p in proxies]),
        data_limit_reset_strategy=escape_html(data_limit_reset_strategy),
    )

    return report(
        chat_id=admin.telegram_id if admin and admin.telegram_id else None,
        text=text,
        keyboard=BotKeyboard.user_menu({'username': username, 'status': 'active'}, with_back=False))


def report_user_deletion(username: str, by: str, admin: Admin = None):
    text = '''\
🗑 <b>#Deleted</b>
➖➖➖➖➖➖➖➖➖
<b>Username</b> : <code>{username}</code>
➖➖➖➖➖➖➖➖➖
<b>Belongs To :</b> <code>{belong_to}</code>
<b>By</b> : <b>#{by}</b>\
    '''.format(
        belong_to=escape_html(admin.username) if admin else None,
        by=escape_html(by),
        username=escape_html(username)
    )
    return report(chat_id=admin.telegram_id if admin and admin.telegram_id else None, text=text)


def report_status_change(username: str, status: str, admin: Admin = None):
    _status = {
        'active': '✅ <b>#Activated</b>',
        'disabled': '❌ <b>#Disabled</b>',
        'limited': '🪫 <b>#Limited</b>',
        'expired': '🕔 <b>#Expired</b>'
    }
    text = '''\
{status}
➖➖➖➖➖➖➖➖➖
<b>Username</b> : <code>{username}</code>
<b>Belongs To :</b> <code>{belong_to}</code>\
    '''.format(
        belong_to=escape_html(admin.username) if admin else None,
        username=escape_html(username),
        status=_status[status]
    )
    return report(chat_id=admin.telegram_id if admin and admin.telegram_id else None, text=text)


def report_user_usage_reset(username: str, by: str, admin: Admin = None):
    text = """  
🔁 <b>#Reset</b>
➖➖➖➖➖➖➖➖➖
<b>Username</b> : <code>{username}</code>
➖➖➖➖➖➖➖➖➖
<b>Belongs To :</b> <code>{belong_to}</code>
<b>By</b> : <b>#{by}</b>\
    """.format(
        belong_to=escape_html(admin.username) if admin else None,
        by=escape_html(by),
        username=escape_html(username)
    )
    return report(chat_id=admin.telegram_id if admin and admin.telegram_id else None, text=text)


def report_user_subscription_revoked(username: str, by: str, admin: Admin = None):
    text = """  
🔁 <b>#Revoked</b>
➖➖➖➖➖➖➖➖➖
<b>Username</b> : <code>{username}</code>
➖➖➖➖➖➖➖➖➖
<b>Belongs To :</b> <code>{belong_to}</code>
<b>By</b> : <b>#{by}</b>\
    """.format(
        belong_to=escape_html(admin.username) if admin else None,
        by=escape_html(by),
        username=escape_html(username)
    )
    return report(chat_id=admin.telegram_id if admin and admin.telegram_id else None, text=text)


def report_login(username: str, password: str, client_ip: str, status: str):
    text = """  
🔐 <b>#Login</b>
➖➖➖➖➖➖➖➖➖
<b>Username</b> : <code>{username}</code>
<b>Password</b> : <code>{password}</code>
<b>Client ip </b>: <code>{client_ip}</code>
➖➖➖➖➖➖➖➖➖
<b>login status </b>: <code>{status}</code>  
    """.format(
        username=escape_html(username),
        password=escape_html(password),
        status=escape_html(status),
        client_ip=escape_html(client_ip)
    )
    return report(text=text)
