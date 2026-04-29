# bot/webhook.py - update the import
from bot.bot import get_app

_app = None

async def process_update(update_data: dict):
    global _app
    if _app is None:
        _app = get_app()
    if not _app.running:
        await _app.initialize()
        await _app.start()
    update = Update.de_json(update_data, _app.bot)
    await _app.process_update(update)