import time
import aiohttp
from aiohttp import web

BOT_TOKEN = "8083363256:AAEmJvaHO_3ecDWHT26QTdvOpjhOXl2LvtE"


async def telegram_ping():
    """Ping Telegram Bot API and return latency in ms."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

    try:
        start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                await resp.text()
        return round((time.time() - start) * 1000, 2)
    except:
        return None


async def handle_root(request):
    """Main endpoint '/'."""
    ping = await telegram_ping()

    if ping is None:
        return web.json_response({"ok": False, "ping_ms": None, "error": "telegram unreachable"}, status=500)

    return web.json_response({"ok": True, "ping_ms": ping})


async def init_app():
    app = web.Application()
    app.router.add_get("/", handle_root)
    return app


def main():
    print("HTTP server running on port 8000...")
    web.run_app(init_app(), host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
