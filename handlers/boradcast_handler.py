import logging
from services.user_service import get_all_users

def broadcast(update, context):
   if update.effective_user.id not in ADMIN_IDS:
       update.message.reply_text("You are not authorized to use this command.")
       return
   
   message = ' '.join(context.args)
   
   if message:
       all_users = get_all_users()  
       for user_id in all_users:
           try:
               app.send_message(chat_id=user_id, text=message)
           except Exception as e:
               logging.error(f"Failed to send broadcast to user {user_id}: {e}")
       
       app.send_message(chat_id=LOG_CHANNEL, text=f"Broadcasting message: {message}")
       
       update.message.reply_text(f"Broadcasting message: {message}")
   else:
       update.message.reply_text("Please provide a message to broadcast.")
