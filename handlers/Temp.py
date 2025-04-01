# start_handler.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

def start(update: Update, context: ContextTypes):
    keyboard = [
        [InlineKeyboardButton("Help", callback_data="help")],
        [InlineKeyboardButton("Force Join", url=f"https://t.me/{FORCE_SUB}") if FORCE_SUB!= "0" else None]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        update.effective_message.reply_text(
            "Welcome to the Advanced Hybrid Bot!\nUse /help to see available commands.",
            reply_markup=reply_markup,
        )
    except Exception as e:
        logging.error(f"Error sending start message: {e}")

# stats_handler.py
from telegram import Update
from telegram.ext import ContextTypes

def stats(update: Update, context: ContextTypes):
    if update.effective_user.id not in ADMIN_IDS:
        update.effective_message.reply_text("You are not authorized to view stats.")
        return
    
    total_files = count_total_files()   # Replace with actual count logic from your storage mechanism
    
    stats_message = f"""
    Bot Stats:
    Total Files Stored: {total_files}
    Total Users Served: {len(ADMIN_IDS)}  
    """
    
    update.effective_message.reply_text(stats_message)

def count_total_files():
    # Logic here to count total files stored in DB_CHANNEL or another source of truth
    return total_count_of_files()

# autofiler_handler.py
import logging
from config import DB_CHANNEL
from telegram import Update
from telegram.ext import ContextTypes

def auto_filter_files(update: Update, context: ContextTypes):
    query =''.join(context.args).lower()  # Get user query
    
    if not query:
        update.effective_message.reply_text("Please provide a search query.")
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
            
            update.effective_message.reply_text(response_message)
        else:
            update.effective_message.reply_text("No files found matching your query.")
    except Exception as e:
        logging.error(f"Error fetching files: {e}")
        update.effective_message.reply_text("An error occurred while searching for files.")

# ban_handler.py
from config import ADMIN_IDS
from telegram import Update
from telegram.ext import ContextTypes

def ban_user(update: Update, context: ContextTypes):
    if update.effective_user.id not in ADMIN_IDS:
        update.effective_message.reply_text("You are not authorized to use this command.")
        return
    
    try:
        user_id = int(context.args[0])
        
        context.bot.send_message(chat_id=LOG_CHANNEL, text=f"User {user_id} has been banned.")
        
        update.effective_message.reply_text(f"User {user_id} banned successfully.")
        
        # Logic to ban the user from the bot can be added here

    except IndexError:
        update.effective_message.reply_text("Please provide a valid user ID.")

# batch_handler.py
import logging
from config import ADMIN_IDS, DB_CHANNEL, AUTO_DELETE_TIME
from services.file_service import delete_file_after_time, cleanup_temp_files
from telegram import Update
from telegram.ext import ContextTypes

def first_batch(update: Update, context: ContextTypes):
    if update.effective_user.id not in ADMIN_IDS:
        update.effective_message.reply_text("You are not authorized to use this command.")
        return
    
    context.user_data['batch_files'] = []
    update.effective_message.reply_text("Please send the files you want to include in this batch.")

def last_batch(update: Update, context: ContextTypes):
    if 'batch_files' not in context.user_data or not context.user_data['batch_files']:
        update.effective_message.reply_text("No files have been added to the batch.")
        return

    for file_id in context.user_data['batch_files']:
        try:
            message = context.bot.send_document(chat_id=DB_CHANNEL, document=file_id, protect_content=True)
            # Schedule auto-delete after specified time.
            context.job_queue.run_once(delete_file_after_time, AUTO_DELETE_TIME, context=(DB_CHANNEL, message.message_id))
        except Exception as e:
            logging.error(f"Error uploading batch file: {e}")

    del context.user_data['batch_files']
    update.effective_message.reply_text("Batch upload completed!")

    # Clean up temporary files after processing (if applicable)
    cleanup_temp_files()  

def handle_document(update: Update, context: ContextTypes):
    if 'batch_files' in context.user_data:
        context.user_data['batch_files'].append(update.message.document.file_id)
        update.effective_message.reply_text(f"Added {update.message.document.file_name} to batch.")

# broadcast_handler.py
import logging
from services.user_service import get_all_users
from telegram import Update
from telegram.ext import ContextTypes

def broadcast(update: Update, context: ContextTypes):
    if update.effective_user.id not in ADMIN_IDS:
        update.effective_message.reply_text("You are not authorized to use this command.")
        return
    
    message =''.join(context.args)
    
    if message:
        all_users = get_all_users()  
        for user_id in all_users:
            try:
                context.bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                logging.error(f"Failed to send broadcast to user {user_id}: {e}")
        
        context.bot.send_message(chat_id=LOG_CHANNEL, text=f"Broadcasting message: {message}")
        
        update.effective_message.reply_text(f"Broadcasting message: {message}")
    else:
        update.effective_message.reply_text("Please provide a message to broadcast.")

# getlink_handler.py
import logging
from config import ADMIN_IDS, DB_CHANNEL, AUTO_DELETE_TIME
from services.file_service import delete_file_after_time, cleanup_temp_files
from telegram import Update
from telegram.ext import ContextTypes

def getlink_handler(update: Update, context: ContextTypes):
    if update.effective_user.id not in ADMIN_IDS:
        update.effective_message.reply_text("You are not authorized to use this command.")
        return
    
    if update.message.reply_to_message and update.message.reply_to_message.document:
        file_id = update.message.reply_to_message.document.file_id
        
        try:
            # Validate file type and size before uploading (add your own criteria)
            document_size = update.message.reply_to_message.document.file_size
            
            if document_size > 50 * 1024 * 1024:  # Example: limit to 50 MB
                update.effective_message.reply_text("File size exceeds the maximum limit of 50 MB.")
                return
            
            # Upload file to DB_CHANNEL
            message = context.bot.send_document(chat_id=DB_CHANNEL, document=file_id, protect_content=True)
            
            # Generate correct link format for accessing messages in channels
            link = f"https://t.me/c/{str(DB_CHANNEL)[4:]}/{message.message_id}"  
            
            # Schedule auto-delete after specified time
            context.job_queue.run_once(delete_file_after_time, AUTO_DELETE_TIME, context=(DB_CHANNEL, message.message_id))
            
            update.effective_message.reply_text(f"File uploaded successfully! Access it here:\n{link}")
            
            # Clean up temporary files after processing (if applicable)
            cleanup_temp_files()  
        except Exception as e:
            logging.error(f"Error uploading file: {e}")
            update.effective_message.reply_text("Failed to upload file.")

# help_handler.py
from telegram import Update
from telegram.ext import ContextTypes

def help(update: Update, context: ContextTypes):
    commands = """
    Available Commands:
    /getlink - Store a single file.
    /firstbatch - Start batch upload (reply to first file).
    /lastbatch - End batch upload (reply to last file).
    /broadcast <message> - Send a message to all users (Admins only).
    /stats - View bot stats (Admins only).
    /ban <user_id> - Ban a user (Admins only).
    /restart or /repair - Restart/repair the bot automatically.
    /setpersonality <type> - Set personality for group chat interaction.
    """
    
    update.effective_message.reply_text(commands)

# personality_handler.py
from personalities.personality_responses import respond_based_on_personality
from telegram import Update
from telegram.ext import ContextTypes

def set_personality(update: Update, context: ContextTypes):
    if len(context.args) == 0 or context.args[0] not in PERSONALITIES.keys():
        update.effective_message.reply_text(f"Available personalities: {', '.join(PERSONALITIES.keys())}")
        return
    
    personality_type = context.args[0]
    
    response = respond_based_on_personality(personality_type)
    
    update.effective_message.reply_text(response)

# restart_handler.py
import os
import sys
from telegram import Update
from telegram.ext import ContextTypes

def restart_bot(update: Update, context: ContextTypes):
    if update.effective_user.id not in ADMIN_IDS:
        update.effective_message.reply_text("You are not authorized to use this command.")
        return
    
    try:
        update.effective_message.reply_text("Restarting bot...")
        
        os.execv(sys.executable, ['python'] + sys.argv)
    
    except Exception as e:
        logging.error(f"Failed to restart bot: {e}")
