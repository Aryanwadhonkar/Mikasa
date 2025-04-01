import logging
from config import DB_CHANNEL

def auto_filter_files(update, context):
    query = ' '.join(context.args).lower()  # Get user query
    
    if not query:
        update.message.reply_text("Please provide a search query.")
        return
    
    try:
        # Fetch messages from DB_CHANNEL
        messages = context.bot.get_chat_history(chat_id=DB_CHANNEL, limit=100)  # Adjust limit as needed
        
        # Filter messages based on query
        filtered_files = [
            msg for msg in messages if msg.document and (
                query in (msg.caption or "").lower() or query in msg.document.file_name.lower()
            )
        ]
        
        if filtered_files:
            response_message = "Found files:\n"
            for file_msg in filtered_files:
                response_message += f"- {file_msg.document.file_name}: https://t.me/c/{str(DB_CHANNEL)[4:]}/{file_msg.message_id}\n"
            
            update.message.reply_text(response_message)
        else:
            update.message.reply_text("No files found matching your query.")
    except Exception as e:
        logging.error(f"Error fetching files: {e}")
        update.message.reply_text("An error occurred while searching for files.")
