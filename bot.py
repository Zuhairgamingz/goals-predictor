import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os


TOKEN = os.getenv("TOKEN") or '7948540215:AAGHaPFqn2Sdmy0OCJwlHsuOHZLvy_pIwUk'  # Railway injects this


# ----------- HEX → 256-bit binary -----------
def sha256hex_to_bits(hexhash: str) -> str:
    return bin(int(hexhash, 16))[2:].zfill(256)


def result_25_bits_from_hex(hexhash: str) -> str:
    bits = sha256hex_to_bits(hexhash)
    return bits[:25]  # first 25 bits (mines)


def result_50_bits_from_hex(hexhash: str) -> str:
    bits = sha256hex_to_bits(hexhash)
    return bits[:50]  # first 50 bits (goals)


# ----------- Start Command -----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("25bits mines", callback_data="25")],
        [InlineKeyboardButton("50bits goals", callback_data="50")]
    ]

    await update.message.reply_text(
        "Send me an *encrypted SHA-256 hex* and choose output type:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ----------- Mode Selection -----------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode = query.data
    context.user_data["mode"] = mode

    await query.edit_message_text(
        f"Send your *encrypted SHA-256* for **{mode}-bit result**:",
        parse_mode="Markdown"
    )

    context.user_data["waiting"] = True


# ----------- Validate & Process Hex Input -----------
async def hex_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting"):
        return

    hexhash = update.message.text.strip().lower()

    # Validate SHA256 hex
    if not re.fullmatch(r"[0-9a-f]{64}", hexhash):
        await update.message.reply_text(
            "❌ Invalid hash!\nMust be **64 hex characters** (SHA-256).")
        return

    mode = context.user_data["mode"]

    if mode == "25":
        result = result_25_bits_from_hex(hexhash)
        label = "25-bit mines"
    else:
        result = result_50_bits_from_hex(hexhash)
        label = "50-bit goals"

    keyboard = [
        [InlineKeyboardButton("25bits mines", callback_data="25")],
        [InlineKeyboardButton("50bits goals", callback_data="50")],
        [InlineKeyboardButton("Exit", callback_data="exit")]
    ]

    await update.message.reply_text(
        f"✅ Result for **{label}**:\n```\n{result}\n```",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    context.user_data["waiting"] = False


# ----------- Exit Handler -----------
async def exit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("Session ended.\nUse /start to begin again.")


# ----------- Main -----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler, pattern="25"))
    app.add_handler(CallbackQueryHandler(menu_handler, pattern="50"))
    app.add_handler(CallbackQueryHandler(exit_handler, pattern="exit"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, hex_input))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
