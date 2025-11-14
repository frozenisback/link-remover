import re
import asyncio
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

# EXACT same protected IDs
PROTECTED_USER_IDS = [777000, 5268762773]

# EXACT same regex patterns
urlRegex = re.compile(r"(https?:\/\/[^\s]+)")
tmeRegex = re.compile(r"(t\.me\/[^‌]+)")
mentionRegex = re.compile(r"@\w+")

# Telethon client
client = TelegramClient("linkremo2ver_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


# ------------------------------
# Delete Message + Notify
# ------------------------------
async def delete_and_notify(event, from_user, reason):
    try:
        await event.delete()
    except MessageDeleteForbiddenError:
        pass

    name = getattr(from_user, "first_name", None) or getattr(from_user, "title", None) or "User"

    await client.send_message(
        event.chat_id,
        f'<a href="tg://user?id={from_user.id}">{name}</a>, your message was deleted because {reason}',
        parse_mode='html',
        buttons=[
            [Button.url("✨Protect your group 💕", "https://t.me/linkremoverlbot?startgroup=true")]
        ]
    )


# ------------------------------
# EXACT JS LOGIC → IN PYTHON + RAW HTTP API FIX
# ------------------------------
async def resolve_username_via_http(username):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat?chat_id=@{username}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            try:
                data = await resp.json()
            except:
                return None

            if not data.get("ok"):
                return None

            return data.get("result", None)


async def checkAndHandleContent(event, text, from_user):
    if from_user.id in PROTECTED_USER_IDS:
        print(f"Skipping protected user {from_user.id}")
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

            # Ends with bot immediately
            if username.lower().endswith("bot"):
                isDeleted = True
                reason = 'it mentioned a "bot".'
                break

            # ---- RAW HTTP API CHECK ----
            entity = await resolve_username_via_http(username)

            if entity:
                etype = entity.get("type", "")

                if etype in ["channel", "supergroup", "group"]:
                    isDeleted = True
                    reason = "it mentioned a group or channel."
                    break

                if etype == "bot":
                    isDeleted = True
                    reason = 'it mentioned a "bot".'
                    break
            # ----------------------------

    if isDeleted:
        await delete_and_notify(event, from_user, reason)


# ------------------------------
# /start COMMAND (EXACT SAME)
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
# CALLBACK QUERIES (UNCHANGED)
# ------------------------------
@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode("utf-8")

    if data == "help":
        helpMessage = (
            "<b>👋 Hello, I'm <i>LinkRemover Bot</i> 🤖!</b>\n\n"
            "<blockquote>🔒 Keep your group safe from unwanted links and bot spam!</blockquote>\n"
            "<blockquote>🚀 Automatically detects and removes links, bot usernames, and group/channel mentions.</blockquote>\n\n"
            "<b>✨ Features:</b>\n"
            "<blockquote>✅ Deletes messages containing links (URLs).</blockquote>\n"
            "<blockquote>✅ Removes mentions of <u>bots</u>, <u>channels</u>, or <u>groups</u>.</blockquote>\n"
            "<blockquote>✅ Lightweight and efficient.</blockquote>\n\n"
            "<b>📖 How to Use:</b>\n"
            "<blockquote>➤ Add me to your group.</blockquote>\n"
            "<blockquote>➤ Make me an admin.</blockquote>\n\n"
            "<b>🔗 Links:</b>\n"
            "<blockquote>💬 <a href='https://t.me/Frozensupport1'>Support Group</a></blockquote>\n"
            "<blockquote>🌐 <a href='https://t.me/linkremoverallbot?startgroup=true'>Add Me to Your Group</a></blockquote>\n\n"
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
# MAIN MESSAGE HANDLER
# ------------------------------
@client.on(events.NewMessage)
async def message_handler(event):
    if not event.text:
        return

    text = event.text
    from_user = await event.get_sender()

    print(f"Received from {from_user.username}: {text}")

    await checkAndHandleContent(event, text, from_user)


print("Bot running with Telethon (long polling)...")
client.run_until_disconnected()
