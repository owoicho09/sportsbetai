from telegram import Update
from bot.bot import get_app

# Initialize once at module load
_app = get_app()


async def process_update(update_data: dict):
    # Only initialize once
    if not _app.initialized:
        await _app.initialize()

    update = Update.de_json(update_data, _app.bot)

    # Process update only
    await _app.process_update(update)