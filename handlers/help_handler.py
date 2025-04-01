def help(update, context):
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
    
    update.message.reply_text(commands)
