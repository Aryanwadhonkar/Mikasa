from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Help", callback_data="help")],
        [InlineKeyboardButton("Force Join", url=f"https://t.me/{FORCE_SUB}") if FORCE_SUB != "0" else None]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        update.message.reply_text(
            "Welcome to the Advanced Hybrid Bot!\nUse /help to see available commands.",
            reply_markup=reply_markup,
        )
    except Exception as e:
        logging.error(f"Error sending start message: {e}")
