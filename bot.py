import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)

# USER STATES
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


# --- Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = {"period": None, "column": 1}

    await update.message.reply_text(
        "Send the *period number* for this round.",
        parse_mode="Markdown"
    )


# --- Period Number Handler ---
async def handle_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not update.message.text.isdigit():
        return await update.message.reply_text("Send a valid period number.")

    user_state[user_id]["period"] = int(update.message.text)

    keyboard = [
        [InlineKeyboardButton("Predict Column 1", callback_data="predict")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Period saved! ✔️\n\nClick below to start prediction:",
        reply_markup=markup
    )


# --- Prediction Handler ---
async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    state = user_state[user_id]

    if not state["period"]:
        return await query.edit_message_text("Send period number first.")

    column = state["column"]
    period = state["period"]

    row, conf = simulate_safest_row(column, period)

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
    state = user_state[user_id]

    if state["column"] < 9:
        state["column"] += 1

    await predict(update, context)


# --- New Game ---
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_state[query.from_user.id] = {"period": None, "column": 1}

    await query.edit_message_text(
        "Game reset! Send a new period number to start again."
    )


# --- Main ---
def main():
    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^[0-9]+$"), handle_period))
    app.add_handler(CallbackQueryHandler(predict, pattern="predict"))
    app.add_handler(CallbackQueryHandler(next_column, pattern="next"))
    app.add_handler(CallbackQueryHandler(new_game, pattern="newgame"))

    app.run_polling()


if __name__ == "__main__":
    main()
