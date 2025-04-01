import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from config import BOT_TOKEN

# Import handlers from the handlers module.
from handlers.start_handler import start_handler
from handlers.help_handler import help_handler
from handlers.getlink_handler import getlink_handler
from handlers.batch_handler import first_batch_handler, last_batch_handler, handle_document_handler
from handlers.broadcast_handler import broadcast_handler
from handlers.stats_handler import stats_handler
from handlers.ban_handler import ban_user_handler
from handlers.personality_handler import set_personality_handler
from handlers.restart_handler import restart_bot_handler

# Initialize logging.
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Create Updater and Dispatcher.
updater = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher

# Register all handlers.
try:
    dispatcher.add_handler(CommandHandler('start', start_handler))
    dispatcher.add_handler(CommandHandler('help', help_handler))
    dispatcher.add_handler(CommandHandler('getlink', getlink_handler))
    dispatcher.add_handler(CommandHandler('firstbatch', first_batch_handler))
    dispatcher.add_handler(CommandHandler('lastbatch', last_batch_handler))
    dispatcher.add_handler(MessageHandler(Filters.document & Filters.reply, handle_document_handler))
    dispatcher.add_handler(CommandHandler('broadcast', broadcast_handler))
    dispatcher.add_handler(CommandHandler('stats', stats_handler))
    dispatcher.add_handler(CommandHandler('ban', ban_user_handler))
    dispatcher.add_handler(CommandHandler('setpersonality', set_personality_handler))
    dispatcher.add_handler(CommandHandler('restart', restart_bot_handler))
except Exception as e:
    logging.error(f"Error registering commands: {e}")

# Start polling for updates.
try:
    updater.start_polling()
    updater.idle()
except Exception as e:
    if "Unauthorized" in str(e):
        logging.error("Invalid BOT_TOKEN. Please check your configuration.")
    else:
        logging.error(f"Error starting the bot: {e}")
