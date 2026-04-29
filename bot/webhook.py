from telegram import Update
from bot.bot import get_app

_app = get_app()

_initialized = False


async def process_update(update_data: dict):
    global _initialized

    # Initialize ONLY once
    if not _initialized:
        await _app.initialize()
        _initialized = True

    update = Update.de_json(update_data, _app.bot)

    await _app.process_update(update)