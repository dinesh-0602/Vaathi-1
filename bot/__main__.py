import os
import shutil, psutil
import signal
from sys import executable
from datetime import datetime
from quoters import Quote
import asyncio
import time
import pytz

from pyrogram import idle
from telegram.ext import CommandHandler
from telegram.error import BadRequest, Unauthorized
from telegram import ParseMode

from bot import bot, app, dispatcher, updater, botStartTime, IGNORE_PENDING_REQUESTS, TIMEZONE, AUTHORIZED_CHATS
from bot.helper.ext_utils import fs_utils
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import *
from .helper.telegram_helper.filters import CustomFilters
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from bot.helper.telegram_helper import button_build
from .modules import authorize, list, cancel_mirror, mirror_status, mirror, clone, watch, shell, speedtest, eval, delete, reboot
now=datetime.now(pytz.timezone(f'{TIMEZONE}'))


def stats(update, context):
    currentTime = get_readable_time(time.time() - botStartTime)
    total, used, free = shutil.disk_usage(".")
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    stats = (
        f"<b>Bot Uptime:</b> {currentTime}\n"
        f"<b>Total disk space:</b> {total}\n"
        f"<b>Used:</b> {used}  "
        f"<b>Free:</b> {free}\n\n"
        f"Data Usage\n<b>Upload:</b> {sent}\n"
        f"<b>Down:</b> {recv}\n\n"
        f"<b>CPU:</b> {cpuUsage}% "
        f"<b>RAM:</b> {memory}% "
        f"<b>Disk:</b> {disk}%"
    )
    sendMessage(stats, context.bot, update)


def start(update, context):
    buttons = button_build.ButtonMaker()
    buttons.buildbutton("Owner", "https://t.me/kaiipulla")
    buttons.buildbutton("Channel", "https://t.me/VaathiCloud")
    reply_markup = InlineKeyboardMarkup(buttons.build_menu(2))
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        start_string = f'''
This bot can mirror all your links to Google Drive!
Type /{BotCommands.HelpCommand} to get a list of available commands
'''
        sendMarkup(start_string, context.bot, update, reply_markup)
    else:
        sendMarkup(
            'Oops! not a Authorized user.',
            context.bot,
            update,
            reply_markup,
        )

    sendMessage(start_string, context.bot, update)


def restart(update, context):
    restart_message = sendMessage("Restarting, Please wait!", context.bot, update)
    # Save restart message ID and chat ID in order to edit it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    fs_utils.clean_all()
    os.execl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update)
    end_time = int(round(time.time() * 1000))
    editMessage(f"{end_time - start_time} ms", reply)


def log(update, context):
    sendLogFile(context.bot, update)


def bot_help(update, context):
    help_string = f"""
/{BotCommands.MirrorCommand} [download_url][magnet_link]: Start mirroring the link to google drive.
Plzzz see this for full use of this command https://telegra.ph/Magneto-Python-Aria---Custom-Filename-Examples-01-20

/{BotCommands.UnzipMirrorCommand} [download_url][magnet_link] : starts mirroring and if downloaded file is any archive , extracts it to google drive

/{BotCommands.ZipMirrorCommand} [download_url][magnet_link]: start mirroring and upload the archived (.tar) version of the download

/{BotCommands.WatchCommand} [youtube-dl supported link]: Mirror through youtube-dl. Click /{BotCommands.WatchCommand} for more help.

/{BotCommands.ZipWatchCommand} [youtube-dl supported link]: Mirror through youtube-dl and tar before uploading

/{BotCommands.CancelMirror} : Reply to the message by which the download was initiated and that download will be cancelled

/{BotCommands.StatusCommand}: Shows a status of all the downloads

/{BotCommands.ListCommand} [search term]: Searches the search term in the Google drive, if found replies with the link

/{BotCommands.StatsCommand}: Show Stats of the machine the bot is hosted on

/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Can only be invoked by owner of the bot)

/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports

"""
    sendMessage(help_string, context.bot, update)


botcmds = [
        (f'{BotCommands.MirrorCommand}', 'Start Mirroring'),
        (f'{BotCommands.ZipMirrorCommand}', 'Start mirroring and upload as .zip'),
        (f'{BotCommands.UnzipMirrorCommand}', 'Extract files'),
        (f'{BotCommands.CloneCommand}', 'Copy file/folder to Drive'),
        (f'{BotCommands.deleteCommand}', 'Delete file from Drive'),
        (f'{BotCommands.WatchCommand}', 'Mirror yt-dlp support link'),
        (f'{BotCommands.ZipWatchCommand}', 'Zip Youtube Video'),
        (f'{BotCommands.CancelMirror}', 'Cancel a task'),
        (f'{BotCommands.CancelAllCommand}', 'Cancel all tasks'),
        (f'{BotCommands.ListCommand}', 'Searches files in Drive'),
        (f'{BotCommands.StatusCommand}', 'Get Mirror Status message'),
        (f'{BotCommands.StatsCommand}', 'Bot Usage Stats'),
        (f'{BotCommands.RestartCommand}', 'Restart the bot [owner/sudo only]'),
        (f'{BotCommands.LogCommand}', 'Get the Bot Log [owner/sudo only]')
    ]


def main():
    # Heroku restarted
    quo_te = Quote.print()
    GROUP_ID = os.environ.get("AUTHORIZED_CHATS")
    if GROUP_ID is not None and isinstance(GROUP_ID, str):
        try:
            dispatcher.bot.sendMessage(f"{GROUP_ID}", f"𝐁𝐎𝐓 𝐑𝐄𝐒𝐓𝐀𝐑𝐓𝐄𝐃!♻️\n\n𝐐𝐮𝐨𝐭𝐞\n{quo_te}\n\n#Rebooted")
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    fs_utils.start_cleanup()

    # Check if the bot is restarting
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("Restarted successfully!", chat_id, msg_id)
        os.remove(".restartmsg")
    bot.set_my_commands(botcmds)

    start_handler = CommandHandler(
        BotCommands.StartCommand,
        start,
        filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
        run_async=True,
    )
    ping_handler = CommandHandler(
        BotCommands.PingCommand,
        ping,
        filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
        run_async=True,
    )
    restart_handler = CommandHandler(
        BotCommands.RestartCommand,
        restart,
        filters=CustomFilters.owner_filter,
        run_async=True,
    )
    help_handler = CommandHandler(
        BotCommands.HelpCommand,
        bot_help,
        filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
        run_async=True,
    )
    stats_handler = CommandHandler(
        BotCommands.StatsCommand,
        stats,
        filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
        run_async=True,
    )
    log_handler = CommandHandler(
        BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True
    )
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("Bot Started!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)


app.start()
main()
idle()
