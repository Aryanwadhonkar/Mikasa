import logging
from config import ADMIN_IDS, DB_CHANNEL, AUTO_DELETE_TIME
from services.file_service import delete_file_after_time, cleanup_temp_files

def first_batch(update, context):
    if update.effective_user.id not in ADMIN_IDS:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    context.user_data['batch_files'] = []
    update.message.reply_text("Please send the files you want to include in this batch.")

def last_batch(update, context):
    if 'batch_files' not in context.user_data or not context.user_data['batch_files']:
        update.message.reply_text("No files have been added to the batch.")
        return

    for file_id in context.user_data['batch_files']:
        try:
            message = context.bot.send_document(chat_id=DB_CHANNEL, document=file_id, protect_content=True)
            # Schedule auto-delete after specified time.
            context.job_queue.run_once(delete_file_after_time, AUTO_DELETE_TIME, context=(DB_CHANNEL, message.message_id))
        except Exception as e:
            logging.error(f"Error uploading batch file: {e}")

    del context.user_data['batch_files']
    update.message.reply_text("Batch upload completed!")

    # Clean up temporary files after processing (if applicable)
    cleanup_temp_files()  

def handle_document(update, context):
    if 'batch_files' in context.user_data:
        context.user_data['batch_files'].append(update.message.document.file_id)
        update.message.reply_text(f"Added {update.message.document.file_name} to batch.")
