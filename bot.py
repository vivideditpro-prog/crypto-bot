# -*- coding: utf-8 -*-
import os
import logging
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "76291486"))
WALLET_USDT = os.getenv("WALLET_USDT", "0x2f1c79b47fce7f91fca9dfa92030d9c1a85fe2f4")
PRICE_USDT = 10
PRODUCT_NAME = "Crypto Portfolio & PnL Tracker Pro"

ROOT = Path(__file__).resolve().parent

def find_excel_file():
    # Search for any xlsx starting with Crypto_Portfolio or containing Pro
    for pattern in ["Crypto_Portfolio*.xlsx", "*Crypto_Portfolio*.xlsx", "*.xlsx"]:
        matches = list(ROOT.glob(pattern))
        if matches:
            return matches[0]
    return ROOT / "Crypto_Portfolio_and_PnL_Tracker_Pro.xlsx"

PRODUCT_FILE = find_excel_file()

orders = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"🚀 *{PRODUCT_NAME}*\n\n"
        "Professional Excel / Google Sheets tracker for crypto trading and portfolio management.\n"
        "• Real-time PnL tracking\n• Multi-exchange support\n• Automated risk metrics\n\n"
        f"🏷 Price: *{PRICE_USDT} USDT*\n"
        f"💳 Wallet (BEP20/Polygon/EVM):\n`{WALLET_USDT}`\n\n"
        "Click below to purchase:"
    )
    keyboard = [[InlineKeyboardButton(f"Buy Product ({PRICE_USDT} USDT)", callback_data="buy")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "buy":
        user_id = query.from_user.id
        order_id = f"ORD-{user_id}-{int(asyncio.get_event_loop().time())}"
        orders[order_id] = {"user_id": user_id, "status": "pending"}
        text = (
            f"🛒 Order Created: `{order_id}`\n\n"
            f"Please send exactly *{PRICE_USDT} USDT* to:\n`{WALLET_USDT}`\n\n"
            "After payment, notify the admin or wait for confirmation. Admin will approve via command:\n"
            f"`/paid {order_id}`"
        )
        await query.message.reply_text(text, parse_mode="Markdown")

async def paid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /paid <order_id>")
        return
    order_id = context.args[0]
    order = orders.get(order_id)
    if not order:
        await update.message.reply_text("Order not found.")
        return
    
    excel_path = find_excel_file()
    if not excel_path.is_file():
        await update.message.reply_text(f"Product file not found in {ROOT}! Please upload it.")
        return

    order["status"] = "paid"
    try:
        with excel_path.open("rb") as f:
            await context.bot.send_document(
                chat_id=order["user_id"],
                document=f,
                filename="Crypto_Portfolio_and_PnL_Tracker_Pro.xlsx",
                caption=f"✅ Payment confirmed! Here is your {PRODUCT_NAME}."
            )
        order["status"] = "delivered"
        await update.message.reply_text(f"Order {order_id} delivered successfully!")
    except Exception as e:
        log.exception("Delivery failed")
        await update.message.reply_text(f"Error sending file: {e}")

def main():
    if not TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is missing!")
    
    excel_path = find_excel_file()
    if not excel_path.is_file():
        log.warning(f"Warning: Excel file not found initially at {excel_path}. Will search dynamically.")
    else:
        log.info(f"Product file found: {excel_path}")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(CommandHandler("paid", paid_command))
    
    log.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
