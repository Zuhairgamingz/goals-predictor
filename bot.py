import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os

TOKEN = os.getenv("TOKEN") or '7948540215:AAGHaPFqn2Sdmy0OCJwlHsuOHZLvy_pIwUk'  # Railway provides this


# ----------- Correct Base64 decoding (21-byte rule) -----------
def decode_seed(seed):
    # try 1 "="
    try:
        raw = base64.b64decode(seed + "=")
        if len(raw) == 21:
            return raw
    except:
        pass

    # try "=="
    try:
        raw = base64.b64decode(seed + "==")
        if len(raw) == 21:
            return raw
    except:
        pass

    # fallback using mod-4 padding
    missing = len(seed) % 4
    seed2 = seed + "=" * (4 - missing) if missing else seed
    raw = base64.b64decode(seed2)

    # force to 21 bytes (your system standard)
    if len(raw) >= 21:
        return raw[:21]
    return raw


# ----------- Bit converters (big-endian, correct) -----------
def seed_to_25_bits(seed):
    raw = decode_seed(seed)
    binary = ''.join(f'{b:08b}' for b in raw)
    return binary[:25]


def seed_to_50_bits(seed):
    raw = decode_seed(seed)
    binary = ''.join(f'{b:08b}' for b in raw)
    return binary[:50]


# ----------- Start Command -----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("25bits mines", callback_data="25bits")],
        [InlineKeyboardButton("50bits goals", callback_data="50bits")]
    ]
    await update.message.reply_text(
        "Choose your conversion type:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ----------- Mode Selection -----------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "25bits":
        context.user_data["mode"] = "25"
        await query.edit_message_text("Send your seed for **25-bit mines**:", parse_mode="Markdown")

    elif query.data == "50bits":
        context.user_data["mode"] = "50"
        await query.edit_message_text("Send your seed for **50-bit goals**:", parse_mode="Markdown")

    context.user_data["waiting_for_seed"] = True


# ----------- Process Uploaded Seed -----------
async def seed_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("waiting_for_seed"):
        return

    seed = update.message.text.strip()
    mode = context.user_data.get("mode")

    try:
        if mode == "25":
            result = seed_to_25_bits(seed)
            label = "25-bit mines"
        else:
            result = seed_to_50_bits(seed)
            label = "50-bit goals"
    except:
        await update.message.reply_text("❌ Invalid seed! Please send a correct Base64 seed.")
        return

    keyboard = [
        [InlineKeyboardButton("25bits mines", callback_data="25bits")],
        [InlineKeyboardButton("50bits goals", callback_data="50bits")],
        [InlineKeyboardButton("Exit", callback_data="exit")]
    ]

    await update.message.reply_text(
        f"✅ Result for **{label}**:\n```\n{result}\n```",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    context.user_data["waiting_for_seed"] = False


# ----------- Exit Button -----------
async def exit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Session ended.\nUse /start to begin again.")


# ----------- Main Launcher -----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler, pattern="25bits"))
    app.add_handler(CallbackQueryHandler(menu_handler, pattern="50bits"))
    app.add_handler(CallbackQueryHandler(exit_handler, pattern="exit"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, seed_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
