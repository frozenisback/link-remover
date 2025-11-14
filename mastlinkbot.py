import re
import asyncio
import threading
import time
from aiohttp import web
import aiohttp

from telethon import TelegramClient, events, Button
from telethon.errors import (
    MessageDeleteForbiddenError, MessageNotModifiedError,
    UsernameNotOccupiedError, UsernameInvalidError, RPCError
)

# ------------------------------
# CONFIG
# ------------------------------
API_ID = 29568441
API_HASH = "b32ec0fb66d22da6f77d355fbace4f2a"
BOT_TOKEN = "8083363256:AAEmJvaHO_3ecDWHT26QTdvOpjhOXl2LvtE"

PROTECTED_USER_IDS = [777000, 5268762773]

urlRegex = re.compile(r"(https?:\/\/[^\s]+)")
tmeRegex = re.compile(r"(t\.me\/[^‌]+)")
mentionRegex = re.compile(r"@\w+")

# Create Telethon client (NOT started yet)
client = TelegramClient("linkremo2ver_bot", API_ID, API_HASH)


# ------------------------------
# Delete & Notify
# ------------------------------
async def delete_and_notify(event, from_user, reason):
    try:
        await event.delete()
    except:
        pass

    try:
        await client.send_message(
            event.chat_id,
            f'<a href="tg://user?id={from_user.id}">{from_user.first_name}</a>, your message was deleted because {reason}',
            parse_mode='html',
            buttons=[[Button.url("✨Protect your group 💕", "https://t.me/linkremoverlbot?startgroup=true")]]
        )
    except:
        pass


# ------------------------------
# Username Validator
# ------------------------------
def is_valid_username(username):
    if not username:
        return False

    username = username.strip("_").strip()

    if len(username) < 5 or len(username) > 32:
        return False

    if not re.fullmatch(r"[A-Za-z0-9_]+", username):
        return False

    if set(username) == {"_"}:
        return False

    return True


# ------------------------------
# EXACT JS LOGIC → Python
# ------------------------------
async def checkAndHandleContent(event, text, from_user):
    if from_user.id in PROTECTED_USER_IDS:
        return

    isDeleted = False
    reason = ""

    if urlRegex.search(text):
        isDeleted = True
        reason = "it contained a URL."

    if tmeRegex.search(text):
        isDeleted = True
        reason = "it contained a link."

    mentions = mentionRegex.findall(text)
    if mentions:
        for mention in mentions:
            username = mention[1:]

            if username.lower().endswith("bot"):
                isDeleted = True
                reason = 'it mentioned a "bot".'
                break

            if not is_valid_username(username):
                continue

            try:
                ent = await client.get_entity(username)

                if ent.__class__.__name__ in ["Channel", "Chat"]:
                    isDeleted = True
                    reason = "it mentioned a group or channel."
                    break

                if hasattr(ent, "bot") and ent.bot:
                    isDeleted = True
                    reason = "it mentioned a group or channel."
                    break

            except:
                continue

    if isDeleted:
        await delete_and_notify(event, from_user, reason)


# ------------------------------
# Commands & Callbacks
# ------------------------------
@client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    welcomeMessage = (
        "👋 Welcome to LinkRemover Bot! \n\n"
        "<blockquote> 🔒 Protect your groups from unwanted links and bot mentions.</blockquote> \n\n"
        "Select help from below to get more info"
    )

    await event.respond(
        welcomeMessage,
        parse_mode='html',
        buttons=[
            [
                Button.url("✨Add me✨", "https://t.me/linkremoverlbot?startgroup=true"),
                Button.inline("💕Help💕", data="help")
            ],
            [Button.url("🆘Support🆘", "https://t.me/Frozensupport1")]
        ]
    )


@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode("utf-8")

    if data == "help":
        helpMessage = (
            "<b>👋 Hello, I'm <i>LinkRemover Bot</i> 🤖!</b>\n\n"
            "<blockquote>🔒 Keeps your group safe.</blockquote>\n"
            "<b>Happy moderating! 🎉</b>"
        )

        try:
            await event.edit(
                helpMessage,
                parse_mode='html',
                buttons=[[Button.inline("Back", data="back_to_start")]]
            )
        except:
            pass

    elif data == "back_to_start":
        welcomeMessage = (
            "👋 Welcome to LinkRemover Bot! \n\n"
            "<blockquote>Protect your groups from unwanted links and bot mentions.</blockquote>"
        )

        try:
            await event.edit(
                welcomeMessage,
                parse_mode='html',
                buttons=[
                    [
                        Button.url("✨Add me✨", "https://t.me/linkremoverlbot?startgroup=true"),
                        Button.inline("💕Help💕", data="help")
                    ],
                    [Button.url("🆘Support🆘", "https://t.me/Frozensupport1")]
                ]
            )
        except:
            pass


# ------------------------------
# Main Message Handler
# ------------------------------
@client.on(events.NewMessage)
async def message_handler(event):
    if not event.text:
        return

    text = event.text
    from_user = await event.get_sender()

    print(f"Received from {from_user.username}: {text}")
    await checkAndHandleContent(event, text, from_user)


# ------------------------------
# TELEGRAM PING + HTTP SERVER
# ------------------------------
async def telegram_ping():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

    try:
        start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                await resp.text()
        ping = (time.time() - start) * 1000
        return round(ping, 2)
    except:
        return None


async def http_handler(request):
    ping = await telegram_ping()
    return web.json_response({"ok": True, "ping_ms": ping})


async def start_http_server():
    app = web.Application()
    app.router.add_get("/", http_handler)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", 8000)
    print("HTTP server running on port 8000...")
    await site.start()


# ------------------------------
# THREAD: Telethon Loop
# ------------------------------
def telethon_thread():
    with client:
        print("Telethon bot running...")
        client.run_until_disconnected()


# ------------------------------
# MAIN
# ------------------------------
async def main():
    # start telethon in background thread
    threading.Thread(target=telethon_thread, daemon=True).start()

    # start http server in main asyncio loop
    await start_http_server()

    # keep server alive
    while True:
        await asyncio.sleep(3600)


asyncio.run(main())
