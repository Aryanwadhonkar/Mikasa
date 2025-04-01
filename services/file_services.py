import os
import glob
import logging

TEMP_FILE_PATH = "/path/to/temp/files/"  # Replace with actual path where temp files are stored.

def delete_file_after_time(context):
   """Delete a specific file after a scheduled time."""
   try:
       channel_id, message_id = context.job.context 
       app.delete_messages(chat_id=channel_id, message_ids=[message_id])
       logging.info(f"Deleted message {message_id} from channel {channel_id}.")
   except Exception as e:
       logging.error(f"Failed to delete message {message_id}: {e}")

def cleanup_temp_files():
   """Delete all temporary files."""
   temp_files = glob.glob(os.path.join(TEMP_FILE_PATH, "*"))  
   
   for temp_file in temp_files:
       try:
           os.remove(temp_file)
           logging.info(f"Deleted temporary file: {temp_file}")
       except Exception as e:
           logging.error(f"Failed to delete temporary file {temp_file}: {e}")
