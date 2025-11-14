import re
import asyncio
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

client = TelegramClient("linkremo2ver_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


# ------------------------------
# Delete & Notify
# ------------------------------
async def delete_and_notify(event, from_user, reason):
    try:
        await event.delete()
    except MessageDeleteForbiddenError:
        pass

    await client.send_message(
        event.chat_id,
        f'<a href="tg://user?id={from_user.id}">{from_user.first_name}</a>, your message was deleted because {reason}',
        parse_mode='html',
        buttons=[[Button.url("✨Protect your group 💕", "https://t.me/linkremoverlbot?startgroup=true")]]
    )


# ------------------------------
# Mention Username Validator (prevents crashes)
# ------------------------------
def is_valid_username(username):
    if not username:
        return False

    # basic cleanup
    username = username.strip("_").strip()

    if len(username) < 5 or len(username) > 32:
        return False

    if not re.fullmatch(r"[A-Za-z0-9_]+", username):
        return False

    # cannot be only underscores
    if set(username) == {"_"}:
        return False

    return True


# ------------------------------
# Main Logic
# ------------------------------
async def checkAndHandleContent(event, text, from_user):
    if from_user.id in PROTECTED_USER_IDS:
        print(f"Skipping protected {from_user.id}")
        return

    isDeleted = False
    reason = ""

    # URL
    if urlRegex.search(text):
        isDeleted = True
        reason = "it contained a URL."

    # t.me
    if tmeRegex.search(text):
        isDeleted = True
        reason = "it contained a link."

    # Mentions
    mentions = mentionRegex.findall(text)
    if mentions:
        for mention in mentions:
            username = mention[1:]

            # endswith bot
            if username.lower().endswith("bot"):
                isDeleted = True
                reason = 'it mentioned a "bot".'
                break

            # sanitize
            if not is_valid_username(username):
                continue

            # try resolving
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

            except (UsernameNotOccupiedError, UsernameInvalidError, RPCError):
                pass

    if isDeleted:
        await delete_and_notify(event, from_user, reason)


# ------------------------------
# /start command
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


# ------------------------------
# Callback
# ------------------------------
@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode("utf-8")

    if data == "help":
        helpMessage = (
            "<b>👋 Hello, I'm <i>LinkRemover Bot</i> 🤖!</b>\n\n"
            "<blockquote>🔒 Keep your group safe from unwanted links and bot spam!</blockquote>\n"
            "<blockquote>🚀 Automatically detects and removes links, bot usernames, and group/channel mentions.</blockquote>\n\n"
            "<b>Happy moderating! 🎉</b>"
        )

        try:
            await event.edit(
                helpMessage,
                parse_mode='html',
                buttons=[[Button.inline("Back", data="back_to_start")]]
            )
        except MessageNotModifiedError:
            pass

    elif data == "back_to_start":
        welcomeMessage = (
            "👋 Welcome to LinkRemover Bot! \n\n"
            "<blockquote>🔒 Protect your groups from unwanted links and bot mentions.</blockquote> \n\n"
            "Select add me below:"
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
        except MessageNotModifiedError:
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
# HTTP SERVER WITH TELEGRAM PING — endpoint "/"
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


async def handle_root(request):
    ping = await telegram_ping()
    if ping is None:
        return web.json_response({"ok": False, "ping_ms": None})

    return web.json_response({"ok": True, "ping_ms": ping})


async def start_http_server():
    app = web.Application()
    app.router.add_get("/", handle_root)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    print("HTTP Server running on port 8000...")
    await site.start()


# ------------------------------
# MAIN ENTRY
# ------------------------------
async def main():
    # Run HTTP server in background
    asyncio.create_task(start_http_server())

    # Run Telegram bot
    print("Bot running with Telethon (long polling)...")
    await client.run_until_disconnected()


asyncio.run(main())
