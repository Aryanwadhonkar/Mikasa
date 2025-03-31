import os
import sys
import uuid
import time
import logging
import asyncio
import requests
import html
import traceback
from functools import wraps
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember, ChatMemberUpdated, BotCommand, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
    ChatMemberHandler,
    CallbackQueryHandler,
)
from telegram.error import TelegramError

# --- CONFIGURATION ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_CHANNEL = int(os.getenv("DB_CHANNEL"))
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL"))
FORCE_SUB = os.getenv("FORCE_SUB", "0")
DEVELOPER_CHAT_ID = int(os.getenv("DEVELOPER_CHAT_ID", "0"))  # Add this to your .env

if FORCE_SUB != "0":
    try:
        FORCE_SUB = int(FORCE_SUB)
    except Exception:
        FORCE_SUB = FORCE_SUB.strip()

AUTO_DELETE_TIME = int(os.getenv("AUTO_DELETE_TIME", "0"))  # in minutes
URL_SHORTENER_DOMAIN = os.getenv("URL_SHORTENER_DOMAIN")
URL_SHORTENER_API = os.getenv("URL_SHORTENER_API")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMINS", "").split(",") if x.strip()]
LANGUAGE_OPTIONS = {
    "en": "English",
    "hi": "Hindi",
    "de": "German",
    "es": "Spanish",
    "ja": "Japanese",
    "fr": "French",
    "ar": "Arabic",
    "zh": "Chinese",
    "ru": "Russian",
}
DEFAULT_LANGUAGE = "en"
ANIME_GIRL_PERSONALITIES = {
    "tsundere": "Im a bit harsh, but secretly care.",
    "yandere": "I am obsessively in love with you.",
    "kuudere": "I am calm, collected, and emotionless.",
    "dandere": "I am shy and quiet, but I open up.",
}
# --- END CONFIGURATION ---

# --- GLOBAL DATA ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
tokens = {}  # token -> { 'data': file_id or [file_ids], 'timestamp': unix_time, 'type': 'single'|'batch' }
banned_users = set()
premium_members = set()
group_settings = {}  # chat_id -> {'personality': 'tsundere', 'filter_level': 'moderate'}
# --- END GLOBAL DATA ---

def check_credit():
    try:
        with open(__file__, "r", encoding="utf-8") as f:
            code = f.read()
        if "CHEETAH" not in code:
            logger.error("Credit for CHEETAH has been tampered with. Crashing bot.")
            sys.exit("Credit removed")
    except Exception as e:
        logger.error("Credit check failed: " + str(e))
        sys.exit("Credit check failed")

def print_ascii_art():
    art = r"""
    ____ _ _ ______ _______ _ _ _
   / ___| | | | ____|__ __| \ | | |
  | |   | |_| | |__ | | | \| | |
  | |   | _ | __| | | | . ` | |
  | |___| | | | | | | | |\ | |____
   \____|_| |_|_| |_| |_| \_|______|
    """
    print(art)
    print("Developer: @wleaksOwner | GitHub: Aryanwadhonkar/Cheetah")

def shorten_url(long_url: str) -> str:
    try:
        payload = {"url": long_url, "domain": URL_SHORTENER_DOMAIN}
        headers = {"Authorization": f"Bearer {URL_SHORTENER_API}"}
        response = requests.post(f"https://{URL_SHORTENER_DOMAIN}/api", json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("short_url", long_url)
        else:
            return long_url
    except Exception as e:
        logger.error("URL shortening failed: " + str(e))
        return long_url

async def force_sub_check(update: Update, context: CallbackContext) -> bool:
    if FORCE_SUB != "0":
        try:
            member = await context.bot.get_chat_member(FORCE_SUB, update.effective_user.id)
            if member.status == "left":
                keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_SUB}")]]
                await update.message.reply_text("Please join our channel to use this bot.", reply_markup=InlineKeyboardMarkup(keyboard))
                return False
        except TelegramError:
            await update.message.reply_text("Error verifying your subscription. Try again later.")
            return False
    return True

async def start(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type == "private":
        if FORCE_SUB != "0":
            valid = await force_sub_check(update, context)
            if not valid:
                return

        if update.effective_user.id in banned_users:
            await update.message.reply_text("You are banned from using this bot.")
            return

        context.bot_data.setdefault("users", set()).add(update.effective_user.id)
        args = context.args
        if args:
            token = args[0]
            token_data = tokens.get(token)
            if token_data and (time.time() - token_data["timestamp"] <= 86400):
                data = token_data["data"]
                try:
                    if isinstance(data, list):
                        for msg_id in data:
                            await context.bot.copy_message(chat_id=update.effective_chat.id, from_chat_id=DB_CHANNEL, message_id=msg_id, protect_content=True)
                            if AUTO_DELETE_TIME:
                                context.job_queue.run_once(
                                    lambda ctx: asyncio.create_task(ctx.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)),
                                    AUTO_DELETE_TIME * 60,
                                )
                    else:
                        sent_msg = await context.bot.copy_message(chat_id=update.effective_chat.id, from_chat_id=DB_CHANNEL, message_id=data, protect_content=True)
                        if AUTO_DELETE_TIME:
                            context.job_queue.run_once(
                                lambda ctx: asyncio.create_task(ctx.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_msg.message_id)),
                                AUTO_DELETE_TIME * 60,
                            )
                    await context.bot.send_message(chat_id=LOG_CHANNEL, text=f"User {update.effective_user.id} accessed token {token}")
                    del tokens[token]
                except TelegramError as e:
                    logger.error("Error sending file: " + str(e))
                    await update.message.reply_text("Error sending the file. Possibly due to Telegram restrictions.")
            else:
                await update.message.reply_text("Invalid or expired token.")
        else:
            keyboard = [[InlineKeyboardButton(text=LANGUAGE_OPTIONS[lang], callback_data=f"set_language:{lang}") for lang in LANGUAGE_OPTIONS]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Welcome to CHEETAH Bot! Please choose your language:", reply_markup=reply_markup)
    else:
        # Interaction when added to a group
        keyboard = [[InlineKeyboardButton("Set Personality", callback_data="set_personality")] , [InlineKeyboardButton("Set Filter Level", callback_data="set_filter_level")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Hello! I've been added to this group. Admin, please configure me:", reply_markup=reply_markup)

def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext):
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("You are not authorized to use this command.")
            return
        return await func(update, context)
    return wrapped

@admin_only
async def getlink(update: Update, context: CallbackContext) -> None:
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a media message with /getlink")
        return

    msg = update.message.reply_to_message
    file_id = None
    if msg.document:
        file_id = msg.document.file_id
    elif msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.video:
        file_id = msg.video.file_id
    else:
        await update.message.reply_text("No valid media found in replied message.")
        return

    try:
        forwarded = await context.bot.forward_message(chat_id=DB_CHANNEL, from_chat_id=msg.chat.id, message_id=msg.message_id)
        token = str(uuid.uuid4())[:8]
        tokens[token] = {"data": forwarded.message_id, "timestamp": time.time(), "type": "single"}
        special_link = f"https://t.me/{context.bot.username}?start={token}"
        special_link = shorten_url(special_link)
        await update.message.reply_text(f"File stored!\nToken Link: {special_link}", disable_web_page_preview=True)
        await context.bot.send_message(chat_id=LOG_CHANNEL, text=f"Admin {update.effective_user.id} stored a file. Token: {token}")
    except TelegramError as e:
        logger.error("Error in /getlink: " + str(e))
        await update.message.reply_text("Failed to store file due to an error.")

@admin_only
async def firstbatch(update: Update, context: CallbackContext) -> None:
    context.user_data["batch_files"] = []
    await update.message.reply_text("Batch mode started. Send your files and then use /lastbatch to complete.")

@admin_only
async def lastbatch(update: Update, context: CallbackContext) -> None:
    batch_files = context.user_data.get("batch_files", [])
    if not batch_files:
        await update.message.reply_text("No files received for batch.")
        return

    batch_msg_ids = []
    for file_msg in batch_files:
        try:
            forwarded = await context.bot.forward_message(chat_id=DB_CHANNEL, from_chat_id=file_msg.chat.id, message_id=file_msg.message_id)
            batch_msg_ids.append(forwarded.message_id)
        except TelegramError as e:
            logger.error("Error forwarding batch file: " + str(e))

    token = str(uuid.uuid4())[:8]
    tokens[token] = {"data": batch_msg_ids, "timestamp": time.time(), "type": "batch"}
    special_link = f"https://t.me/{context.bot.username}?start={token}"
    special_link = shorten_url(special_link)
    await update.message.reply_text(f"Batch stored!\nToken Link: {special_link}", disable_web_page_preview=True)
    await context.bot.send_message(chat_id=LOG_CHANNEL, text=f"Admin {update.effective_user.id} stored a batch. Token: {token}")
    context.user_data["batch_files"] = []  # Reset batch mode

@admin_only
async def batch_file_handler(update: Update, context: CallbackContext) -> None:
    if "batch_files" in context.user_data:
        context.user_data["batch_files"].append(update.message)
        await update.message.reply_text("File added to batch.")

@admin_only
async def broadcast(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Provide a message to broadcast.")
        return

    message = " ".join(context.args)
    users = context.bot_data.get("users", set())
    sent_count = 0
    for user_id in users:
        try:
            await context.bot.send_message(user_id, message)
            sent_count += 1
        except TelegramError as e:
            logger.error(f"Error sending broadcast to {user_id}: " + str(e))

    await update.message.reply_text(f"Broadcast sent to {sent_count} users.")

@admin_only
async def stats(update: Update, context: CallbackContext) -> None:
    total_users = len(context.bot_data.get("users", set()))
    active_tokens = len(tokens)
    stats_text = f"Total Users: {total_users}\nActive Tokens: {active_tokens}"
    await update.message.reply_text(stats_text)

@admin_only
async def ban(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Provide a user ID to ban.")
        return

    try:
        user_id = int(context.args[0])
        banned_users.add(user_id)
        await update.message.reply_text(f"User {user_id} has been banned.")
        await context.bot.send_message(chat_id=LOG_CHANNEL, text=f"User {user_id} banned by admin {update.effective_user.id}")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

@admin_only
async def premiummembers(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /premiummembers add|remove ")
        return

    action = context.args[0].lower()
    try:
        user_id = int(context.args[1])
        if action == "add":
            premium_members.add(user_id)
            await update.message.reply_text(f"User {user_id} is now a premium member.")
        elif action == "remove":
            premium_members.discard(user_id)
            await update.message.reply_text(f"User {user_id} has been removed from premium members.")
        else:
            await update.message.reply_text("Invalid action. Use add or remove.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")

@admin_only
async def restart(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Restarting bot...")
    await context.bot.send_message(LOG_CHANNEL, f"Bot restarted by admin {update.effective_user.id}")
    os.execv(sys.executable, [sys.executable] + sys.argv)

async def language(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /language ")
        return

    lang = context.args[0].lower()
    if lang in LANGUAGE_OPTIONS:
      context.user_data["language"] = lang
      await update.message.reply_text(f"Language set to {LANGUAGE_OPTIONS[lang]}.")
    else:
      await update.message.reply_text("Invalid Language")

async def post_initializer(application: Application) -> None:
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("getlink", "Get a token link for a file (reply to the file)"),
        BotCommand("firstbatch", "Start a batch file upload"),
        BotCommand("lastbatch", "Finish a batch file upload"),
        BotCommand("broadcast", "Broadcast a message to all users (admin only)"),
        BotCommand("stats", "Show bot statistics (admin only)"),
        BotCommand("ban", "Ban a user (admin only)"),
        BotCommand("premiummembers", "Manage premium members (admin only)"),
        BotCommand("restart", "Restart the bot (admin only)"),
        BotCommand("language", "Set your language"),
    ]
    await application.bot.set_my_commands(commands)

async def new_member_handler(update: Update, context: CallbackContext) -> None:
    """Handles new chat members joining the group."""
    new_members = update.message.new_chat_members
    chat_id = update.effective_chat.id

    for member in new_members:
        if member.is_bot:
            # A bot was added, configure the bot
            keyboard = [[InlineKeyboardButton("Set Personality", callback_data="set_personality")], [InlineKeyboardButton("Set Filter Level", callback_data="set_filter_level")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Thank you for adding me! Admin, please configure my personality and filter level:", reply_markup=reply_markup)
        else:
            # A user joined, welcome them (optional)
            welcome_message = f"Welcome, {member.first_name}, to the group!"
            await context.bot.send_message(chat_id, welcome_message)

async def left_member_handler(update: Update, context: CallbackContext) -> None:
    """Handles chat members leaving the group."""
    chat_id = update.effective_chat.id
    user = update.message.left_chat_member

    # Check if a user or bot left
    if user.is_bot:
        # A bot left, handle accordingly
        await context.bot.send_message(LOG_CHANNEL, f"Bot {user.username} left chat {chat_id}.")
    else:
        # A user left, handle accordingly (e.g., log it)
        await context.bot.send_message(LOG_CHANNEL, f"User {user.first_name} left chat {chat_id}.")

async def chat_member_update_handler(update: Update, context: CallbackContext) -> None:
    """Handles chat member updates, such as a user being banned or unbanned."""
    chat_id = update.effective_chat.id
    user = update.chat_member.new_chat_member.user
    status = update.chat_member.new_chat_member.status

    if status == "kicked":
        # User was banned
        await context.bot.send_message(LOG_CHANNEL, f"User {user.first_name} was banned from chat {chat_id}.")
    elif status == "member":
        # User was unbanned or rejoined
        await context.bot.send_message(LOG_CHANNEL, f"User {user.first_name} rejoined chat {chat_id}.")

async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    data = query.data
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if data.startswith("set_language:"):
        lang = data.split(":")[1]
        context.user_data["language"] = lang
        await query.edit_message_text(f"Language set to {LANGUAGE_OPTIONS[lang]}!")

    elif data == "set_personality":
        if user_id not in ADMIN_IDS:
            await query.answer("Only admins can set the personality.", show_alert=True)
            return
        keyboard = [
            [InlineKeyboardButton(text=personality.capitalize(), callback_data=f"personality:{key}")] for key, personality in ANIME_GIRL_PERSONALITIES.items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Choose the bot's personality:", reply_markup=reply_markup)

    elif data.startswith("personality:"):
        if user_id not in ADMIN_IDS:
            await query.answer("Only admins can set the personality.", show_alert=True)
            return
        personality = data.split(":")[1]
        group_settings[chat_id] = group_settings.get(chat_id, {})
        group_settings[chat_id]["personality"] = personality
        await query.edit_message_text(f"Bot personality set to {personality}.")

    elif data == "set_filter_level":
        if user_id not in ADMIN_IDS:
            await query.answer("Only admins can set the filter level.", show_alert=True)
            return
        keyboard = [
            [InlineKeyboardButton(text="Low", callback_data="filter:low")],
            [InlineKeyboardButton(text="Moderate", callback_data="filter:moderate")],
            [InlineKeyboardButton(text="High", callback_data="filter:high")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Choose the filter level:", reply_markup=reply_markup)

    elif data.startswith("filter:"):
        if user_id not in ADMIN_IDS:
            await query.answer("Only admins can set the filter level.", show_alert=True)
            return
        filter_level = data.split(":")[1]
        group_settings[chat_id] = group_settings.get(chat_id, {})
        group_settings[chat_id]["filter_level"] = filter_level
        await query.edit_message_text(f"Filter level set to {filter_level}.")

async def group_message_handler(update: Update, context: CallbackContext) -> None:
    """Handles messages in group chats, applying the configured personality and filter."""
    chat_id = update.effective_chat.id
    text = update.message.text

    settings = group_settings.get(chat_id, {})
    personality = settings.get("personality", "tsundere")  # Default to tsundere
    filter_level = settings.get("filter_level", "moderate")  # Default to moderate

    # --- PERSONALITY ---
    if personality and text:
        if personality in ANIME_GIRL_PERSONALITIES:
            personality_text = ANIME_GIRL_PERSONALITIES[personality]
            # Basic personality-based response (customize as needed)
            if "hello" in text.lower():
                response_text = f"{personality_text} Hmph, don't think I'm happy you greeted me!"
            elif "thank you" in text.lower():
                response_text = f"{personality_text} It's not like I did it for you or anything!"
            else:
                # Placeholder response
                response_text = f"{personality_text} What do you want?"
            await update.message.reply_text(response_text)
    # --- END PERSONALITY ---

    # --- AUTO FILTER ---
    if filter_level:
        # Basic profanity filter (expand as needed)
        profane_words = ["badword1", "badword2", "badword3"]  # Replace with actual words
        if any(word in text.lower() for word in profane_words):
            if filter_level == "high":
                await update.message.delete()
                await context.bot.send_message(chat_id, "Profanity is not allowed.")
            elif filter_level == "moderate":
                # Mild warning
                await context.bot.send_message(chat_id, "Please refrain from using inappropriate language.")
    # --- END AUTO FILTER ---

def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    try:
        # Collect error information
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = ''.join(tb_list)

        # Build the message
        message = (
            f'An exception was raised while handling an update:\n'
            f'<pre>update = {html.escape(str(update.to_dict()), quote=False)}</pre>\n'
            f'<pre>context.chat_data = {html.escape(str(context.chat_data), quote=False)}</pre>\n'
            f'<pre>context.user_data = {html.escape(str(context.user_data), quote=False)}</pre>\n'
            f'<pre>{html.escape(tb_string, quote=False)}</pre>'
        )

        # Shorten the message if it's too long
        if len(message) > 4096:
            message = message[:4000] + '\n... (message truncated)'

        # Send the message to the developer
        context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML)

    except Exception as ex:
        logger.error("Failed to send error message to developer: %s", str(ex))

def main() -> None:
    check_credit()
    print_ascii_art()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getlink", getlink))
    application.add_handler(CommandHandler("firstbatch", firstbatch))
    application.add_handler(CommandHandler("lastbatch", lastbatch))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("premiummembers", premiummembers))
    application.add_handler(CommandHandler("restart", restart))
    application.add_handler(CommandHandler("language", language))
    application.add_handler(MessageHandler(filters.ALL & filters.ChatType.PRIVATE, batch_file_handler))
    application.add_handler(CallbackQueryHandler(button_callback)) # handles button presses
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUP, group_message_handler))
    application.add_handler(ChatMemberHandler(new_member_handler, ChatMemberHandler.CHAT_MEMBERS))
    application.add_handler(ChatMemberHandler(left_member_handler, ChatMemberHandler.CHAT_MEMBERS))
    application.add_handler(ChatMemberHandler(chat_member_update_handler, ChatMemberHandler.CHAT_MEMBER))
    application.add_error_handler(error_handler)
    application.run_polling(post_init=post_initializer)

if __name__ == '__main__':
    main()
