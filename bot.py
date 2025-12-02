import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os

TOKEN = os.getenv("TOKEN")  # Railway will read token from environment variable


def seed_to_50_bits(seed):
    raw = base64.b64decode(seed)
    binary = ''.join(f'{b:08b}' for b in raw)
    return binary[:50]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Enter Seed", callback_data="enter_seed")]
    ]
    await update.message.reply_text(
        "Welcome! Send me a Base64 seed and I will convert it into a 50-bit result.\n\nPress the button below to start.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "enter_seed":
        await query.edit_message_text("Send your seed now:")
        context.user_data["waiting_for_seed"] = True


async def seed_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_for_seed"):
        return

    seed = update.message.text.strip()

    try:
        result = seed_to_50_bits(seed)
    except:
        await update.message.reply_text("❌ Invalid seed! Must be Base64.")
        return

    keyboard = [
        [InlineKeyboardButton("Enter Another Seed", callback_data="enter_seed")],
        [InlineKeyboardButton("Exit", callback_data="exit")]
    ]

    await update.message.reply_text(
        f"✅ 50-bit result:\n```\n{result}\n```",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    context.user_data["waiting_for_seed"] = False


async def exit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Session ended.\nUse /start to begin again.")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_handler, pattern="enter_seed"))
    app.add_handler(CallbackQueryHandler(exit_handler, pattern="exit"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, seed_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
