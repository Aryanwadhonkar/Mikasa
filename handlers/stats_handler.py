def stats(update, context):
   if update.effective_user.id not in ADMIN_IDS:
       update.message.reply_text("You are not authorized to view stats.")
       return
   
   total_files = count_total_files()   # Replace with actual count logic from your storage mechanism
   
   stats_message = f"""
   Bot Stats:
   Total Files Stored: {total_files}
   Total Users Served: {len(ADMIN_IDS)}  
   """
   
   update.message.reply_text(stats_message)

def count_total_files():
   # Logic here to count total files stored in DB_CHANNEL or another source of truth
   return total_count_of_files()
