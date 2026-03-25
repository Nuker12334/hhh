import os
import logging
import time
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import blooket_api
from web import app

# ----- Configuration -----
TOKEN = os.environ.get("8569463727:AAGs52-W5vrypH9eZAMYdOlVk4jTIgd5o9k")
if not TOKEN:
    raise ValueError("No TELEGRAM_TOKEN environment variable set")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----- Start Flask web server in background (required for Render) -----
def run_web():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_web, daemon=True).start()

# ----- Bot state -----
active_games = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Blooket Bot*\n\n"
        "Send me a game code to join and auto‑answer!\n"
        "Example: `123456`\n\n"
        "_Answers the first option by default._",
        parse_mode="Markdown"
    )

async def handle_game_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = update.message.text.strip()
    if not code.isdigit():
        await update.message.reply_text("Please send a valid game code (numbers only).")
        return

    await update.message.reply_text(f"Joining game {code}...")

    try:
        name = f"Bot_{user_id}"
        result = blooket_api.join_game(code, name)
        game_id = result["gameId"]
        player_id = result["playerId"]
        active_games[user_id] = {
            "game_id": game_id,
            "player_id": player_id,
            "running": True,
            "chat_id": update.effective_chat.id
        }

        await update.message.reply_text(f"✅ Joined game as {name}!\nWaiting for questions...")

        def poll_loop():
            while active_games.get(user_id, {}).get("running"):
                try:
                    q = blooket_api.get_question(game_id, player_id)
                    if q:
                        # Answer the first option (index 0)
                        blooket_api.answer_question(game_id, player_id, q["id"], 0)
                        # Optionally send a message:
                        # context.bot.send_message(chat_id=active_games[user_id]["chat_id"], text=f"Answered: {q['text'][:50]}")
                except Exception as e:
                    logger.error(f"Poll error for user {user_id}: {e}")
                    break
                time.sleep(2)
            # Clean up
            active_games.pop(user_id, None)

        thread = threading.Thread(target=poll_loop, daemon=True)
        thread.start()

    except Exception as e:
        logger.exception("Join failed")
        await update.message.reply_text(f"Failed to join: {e}")

def main():
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game_code))

    logger.info("Bot started. Press Ctrl+C to stop.")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
