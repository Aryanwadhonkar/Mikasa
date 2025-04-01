import os

def restart_bot(update, context):
   if update.effective_user.id not in ADMIN_IDS:
       update.message.reply_text("You are not authorized to use this command.")
       return
   
   try:
       update.message.reply_text("Restarting bot...")
       
       os.execv(sys.executable, ['python'] + sys.argv)
   
   except Exception as e:
       logging.error(f"Failed to restart bot: {e}")
