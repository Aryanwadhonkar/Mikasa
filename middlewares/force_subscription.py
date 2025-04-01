from telegram import Update
from telegram.ext import CallbackContext

def check_subscription(update: Update, context: CallbackContext):
    if FORCE_SUB != "0":
        chat_member = context.bot.get_chat_member(FORCE_SUB, update.effective_user.id)
        if chat_member.status not in ['member', 'administrator']:
            update.message.reply_text("You need to join the channel first: https://t.me/{}".format(FORCE_SUB))
            return False
    return True
