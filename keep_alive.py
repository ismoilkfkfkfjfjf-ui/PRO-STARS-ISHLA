import os
import logging
from aiohttp import web

async def handle_ping(request):
    return web.Response(text="Pro Stars Bot is Running 24/7! ⭐", status=200)

async def handle_health(request):
    return web.json_response({"status": "ok", "bot": "online"})

async def start_web_server(port: int = None):
    if port is None:
        port = int(os.getenv("PORT", 8080))

    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Healthcheck web server started on port {port}")
