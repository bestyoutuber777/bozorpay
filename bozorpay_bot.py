import re
import json
import os
from datetime import datetime, date, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ══════════════════════════════════════
#   SOZLAMALAR — FAQAT SHU YERNI O'ZGARTIRING
# ══════════════════════════════════════
BOT_TOKEN = "8940711746:AAFVCHPk3U-dDMyw6wxvT86SxIIspVvrZvI"
KANAL_ID  = -1003931727916   # Bozor_Pay kanali
# ══════════════════════════════════════

DATA_FILE = "tushumlar.json"

BANK_PATTERNS = [
    {"bank": "Kapital Bank",  "emoji": "🏦", "pattern": r"([\d\s]{4,})\s*(?:UZS|so['\u2019]m|sum|сум)"},
    {"bank": "Ipoteka Bank",  "emoji": "🏠", "pattern": r"([\d\s]{4,})\s*(?:UZS|so['\u2019]m|sum|сум)"},
    {"bank": "Humo",          "emoji": "💳", "pattern": r"([\d\s]{4,})\s*(?:UZS|so['\u2019]m|sum|сум)"},
    {"bank": "UzCard",        "emoji": "💳", "pattern": r"([\d\s]{4,})\s*(?:UZS|so['\u2019]m|sum|сум)"},
    {"bank": "Anor Bank",     "emoji": "🍎", "pattern": r"([\d\s]{4,})\s*(?:UZS|so['\u2019]m|sum|сум)"},
    {"bank": "Bank",          "emoji": "💰", "pattern": r"([\d]{5,})"},
]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"tushumlar": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def parse_sms(text):
    # Bank nomini aniqlash
    bank = "Bank"
    emoji = "💰"
    tl = text.lower()
    if "kapital" in tl:   bank, emoji = "Kapital Bank", "🏦"
    elif "ipoteka" in tl: bank, emoji = "Ipoteka Bank", "🏠"
    elif "humo" in tl:    bank, emoji = "Humo", "💳"
    elif "uzcard" in tl:  bank, emoji = "UzCard", "💳"
    elif "anor" in tl:    bank, emoji = "Anor Bank", "🍎"
    elif "hamkor" in tl:  bank, emoji = "Hamkor Bank", "🤝"
    elif "davr" in tl:    bank, emoji = "Davr Bank", "🏛"
    elif "orient" in tl:  bank, emoji = "Orient Finance", "🌟"

    # Summani topish
    patterns = [
        r"([\d]+[\d\s]*[\d])\s*(?:UZS|so'm|sum|сум|uzs)",
        r"(?:summa|miqdor|amount|kirim|zaxira)[:\s]*([\d\s]+)",
        r"([\d]{5,})",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(" ", "")
            try:
                summa = int(raw)
                if summa >= 1000:
                    return summa, bank, emoji
            except:
                continue
    return None, None, None

def fmt(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f} mln so'm"
    return f"{n:,} so'm".replace(",", " ")

# ── /start ──
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"👋 *BozorPay Bot* ga xush kelibsiz!\n\n"
        f"📨 Bank SMS ini yuboring — kaналга avtomatik xabar ketadi!\n\n"
        f"🆔 Sizning ID: `{chat_id}`",
        parse_mode="Markdown"
    )

# ── SMS QABUL ──
async def sms_qabul(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    summa, bank, emoji = parse_sms(text)

    if summa:
        now = datetime.now()
        data = load_data()

        yozuv = {
            "summa": summa,
            "bank": bank,
            "emoji": emoji,
            "sana": now.date().isoformat(),
            "vaqt": now.strftime("%H:%M"),
        }
        data["tushumlar"].append(yozuv)
        save_data(data)

        # Kanalga xabar
        kanal_xabar = (
            f"💵 *PUL TUSHDI!*\n"
            f"━━━━━━━━━━━━━━\n"
            f"{emoji} Bank: *{bank}*\n"
            f"💰 Summa: *{fmt(summa)}*\n"
            f"📅 Sana: *{now.strftime('%d.%m.%Y')}*\n"
            f"🕐 Vaqt: *{now.strftime('%H:%M')}*"
        )

        try:
            await ctx.bot.send_message(
                chat_id=KANAL_ID,
                text=kanal_xabar,
                parse_mode="Markdown"
            )
            await update.message.reply_text(f"✅ Kaналга yuborildi!\n💰 {fmt(summa)}")
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {e}")
    else:
        await update.message.reply_text(
            "⚠️ SMS formatini tanimayman.\n"
            "Bank SMS ini to'liq yuboring!"
        )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sms_qabul))
    print("✅ BozorPay Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
