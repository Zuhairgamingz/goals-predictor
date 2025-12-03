import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import os


TOKEN = os.getenv("TOKEN") or '7948540215:AAGHaPFqn2Sdmy0OCJwlHsuOHZLvy_pIwUk'  # Railway will inject this


# ---------------- XORSHIFT32 RNG -----------------
def xorshift32(x):
    x &= 0xFFFFFFFF
    x ^= (x << 13) & 0xFFFFFFFF
    x ^= (x >> 17) & 0xFFFFFFFF
    x ^= (x << 5) & 0xFFFFFFFF
    return x & 0xFFFFFFFF


def decode_sha256_to_rows(hexhash):
    # FIRST 4 BYTES = RNG SEED
    seed = int(hexhash[0:8], 16)

    rows = []
    x = seed

    for _ in range(10):
        x = xorshift32(x)
        rows.append(x % 5)   # 0–4 for each column

    return rows


def rows_to_50bits(rows):
    # 5-row one-hot encoding (top row = 0 = 10000)
    patterns = ["10000", "01000", "00100", "00010", "00001"]
    return "".join(patterns[r] for r in rows)


# ---------------- Telegram Bot -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send your *encrypted SHA-256* (64 hex chars) to decode the 50-bit result.",
        parse_mode="Markdown"
    )


async def process_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hexhash = update.message.text.strip().lower()

    # Validate SHA256 hex
    if not re.fullmatch(r"[0-9a-f]{64}", hexhash):
        await update.message.reply_text("❌ Invalid hash! Must be exactly 64 hex characters.")
        return

    # Decode using XORSHIFT32 algorithm
    rows = decode_sha256_to_rows(hexhash)
    bits50 = rows_to_50bits(rows)

    # Show output
    await update.message.reply_text(
        f"✅ 50-bit result:\n```\n{bits50}\n```",
        parse_mode="Markdown"
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_hash))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
