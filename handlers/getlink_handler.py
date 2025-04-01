import logging
from config import ADMIN_IDS, DB_CHANNEL, AUTO_DELETE_TIME
from services.file_service import delete_file_after_time, cleanup_temp_files

def getlink_handler(update, context):
    if update.effective_user.id not in ADMIN_IDS:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    if update.message.reply_to_message and update.message.reply_to_message.document:
        file_id = update.message.reply_to_message.document.file_id
        
        try:
            # Validate file type and size before uploading (add your own criteria)
            document_size = update.message.reply_to_message.document.file_size
            
            if document_size > 50 * 1024 * 1024:  # Example: limit to 50 MB
                update.message.reply_text("File size exceeds the maximum limit of 50 MB.")
                return
            
            # Upload file to DB_CHANNEL
            message = context.bot.send_document(chat_id=DB_CHANNEL, document=file_id, protect_content=True)
            
            # Generate correct link format for accessing messages in channels
            link = f"https://t.me/c/{str(DB_CHANNEL)[4:]}/{message.message_id}"  
            
            # Schedule auto-delete after specified time
            context.job_queue.run_once(delete_file_after_time, AUTO_DELETE_TIME, context=(DB_CHANNEL, message.message_id))
            
            update.message.reply_text(f"File uploaded successfully! Access it here:\n{link}")
            
            # Clean up temporary files after processing (if applicable)
            cleanup_temp_files()  
        except Exception as e:
            logging.error(f"Error uploading file: {e}")
            update.message.reply_text("Failed to upload file.")
