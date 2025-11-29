import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)

# --- Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- User State ---
user_state = {}

# --- Simulation Function ---
def simulate_safest_row(column_index, seed):
    random.seed(seed + column_index)
    rows = [0, 1, 2, 3, 4]
    safe_counts = {r: 0 for r in rows}

    simulations = 10000
    for _ in range(simulations):
        bomb = random.choice(rows)
        for r in rows:
            if r != bomb:
                safe_counts[r] += 1

    safest_row = max(safe_counts, key=lambda x: safe_counts[x])
    confidence = (safe_counts[safest_row] / simulations) * 100
    return safest_row + 1, round(confidence, 2)

# --- /start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = {"period": None, "column": 1}
    await update.message.reply_text(
        "Welcome! Send the *period number* for this round.",
        parse_mode="Markdown"
    )
    logger.info(f"User {update.effective_user.id} started a new game.")

# --- Handle Period Number ---
async def handle_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not update.message.text.isdigit():
        return await update.message.reply_text("Send a valid period number.")

    user_state[user_id]["period"] = int(update.message.text)
    user_state[user_id]["column"] = 1  # Reset column

    keyboard = [[InlineKeyboardButton("Predict Column 1", callback_data="predict")]]
    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Period saved! ✔️\n\nClick below to start prediction:",
        reply_markup=markup
    )
    logger.info(f"User {user_id} set period {update.message.text}")

# --- Prediction Handler ---
async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_state:
        await query.edit_message_text("Please start a new game with /start.")
        return

    state = user_state[user_id]
    if not state.get("period"):
        await query.edit_message_text("Send period number first.")
        return

    column = state["column"]
    period = state["period"]

    row, conf = simulate_safest_row(column, period)
    logger.info(f"User {user_id} column {column}: row {row}, confidence {conf}%")

    keyboard = []
    if column < 9:
        keyboard.append([InlineKeyboardButton("Next Column ▶️", callback_data="next")])
    else:
        keyboard.append([InlineKeyboardButton("New Game 🔄", callback_data="newgame")])

    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"📌 *Prediction for Column {column}:*\n"
        f"🎯 Safe Row: *{row}*\n"
        f"📊 Confidence: *{conf}%*\n\n",
        parse_mode="Markdown",
        reply_markup=markup
    )

# --- Next Column ---
async def next_column(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_state:
        await query.edit_message_text("Please start a new game with /start.")
        return

    if user_state[user_id]["column"] < 9:
        user_state[user_id]["column"] += 1
    await predict(update, context)

# --- New Game ---
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_state[query.from_user.id] = {"period": None, "column": 1}
    await query.edit_message_text(
        "Game reset! Send a new period number to start again."
    )
    logger.info(f"User {query.from_user.id} started a new game.")

# --- Main ---
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set!")

    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_period))
    app.add_handler(CallbackQueryHandler(predict, pattern="predict"))
    app.add_handler(CallbackQueryHandler(next_column, pattern="next"))
    app.add_handler(CallbackQueryHandler(new_game, pattern="newgame"))

    logger.info("Bot started. Polling Telegram...")
    app.run_polling()

if __name__ == "__main__":
    main()
