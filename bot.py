import os
import asyncio
import random
import math
import requests
import feedparser

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ============================
#  ENV VARS
# ============================

TOKEN = os.getenv("TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ============================
#  AI (DeepSeek)
# ============================

def ask_ai(prompt: str) -> str:
    try:
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }

        data = {
            "model": "deepseek-v4-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "Sən Azərbaycan dilində danışan maliyyə köməkçisisən. Cavabları sadə, aydın və konkret ver."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "thinking": {"type": "enabled"},
            "reasoning_effort": "high",
            "stream": False
        }

        r = requests.post(url, json=data, headers=headers, timeout=30)
        r.raise_for_status()
        resp = r.json()

        return resp["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("DEEPSEEK ERROR:", e)
        return "AI cavabında problem yarandı. Bir az sonra yenidən cəhd et."


# ============================
#  AI REJIMLƏRI
# ============================

def build_prompt(user_text: str, mode: str | None) -> str:

    if mode == "kredit":
        return (
            "Sən kredit üzrə ekspert AI-sən. "
            "Faizlər, aylıq ödəniş, ümumi xərc, risklər və müqayisələri izah et. "
            f"Sual: {user_text}"
        )

    if mode == "depozit":
        return (
            "Sən depozit üzrə ekspert AI-sən. "
            "Faiz dərəcələri, gəlirlilik, kapitalizasiya və müqayisələri izah et. "
            f"Sual: {user_text}"
        )

    if mode == "budce":
        return (
            "Sən şəxsi büdcə planlayıcısı AI-sən. "
            "Gəlir-xərc analizi, qənaət, planlama və tövsiyələr ver. "
            f"Sual: {user_text}"
        )

    if mode == "xeber":
        return (
            "Sən maliyyə və iqtisadiyyat üzrə xəbər analitiki AI-sən. "
            "Xəbəri sadə dillə izah et, təsirlərini göstər. "
            f"Mətn: {user_text}"
        )

    if mode == "sade":
        return (
            "Sən izah edən AI-sən. Mövzunu 10 yaşlı uşaq kimi sadə izah et. "
            f"Mövzu: {user_text}"
        )

    # Default
    return (
        "Sən maliyyə üzrə ağıllı assistentsən. "
        "Sualı aydın və konkret cavablandır. "
        f"Sual: {user_text}"
    )


# ============================
#  Tərcümə funksiyası
# ============================

def translate_to_az(text):
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": "en|az"}
        r = requests.get(url, params=params).json()
        return r["responseData"]["translatedText"]
    except:
        return text


# ============================
#  Dinamik xəbər funksiyası
# ============================

async def get_dynamic_news(category):
    sources = []

    if category == "valyuta":
        sources = [
            "https://en.trend.az/rss",
            "https://www.reutersagency.com/feed/?best-topics=business-finance"
        ]
    elif category == "bank":
        sources = [
            "https://apa.az/az/rss",
            "https://report.az/rss/"
        ]
    elif category == "iqtisadiyyat":
        sources = [
            "https://report.az/rss/",
            "https://www.reutersagency.com/feed/?best-topics=business-finance"
        ]
    elif category == "dunya":
        sources = [
            "https://www.reutersagency.com/feed/?best-topics=business-finance",
            "https://www.bloomberg.com/feed/podcast"
        ]

    all_news = []

    for url in sources:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            summary = entry.summary if "summary" in entry else ""
            all_news.append({
                "title": entry.title,
                "summary": summary,
                "link": entry.link
            })

    if not all_news:
        return "Hazırda xəbər tapılmadı."

    news = random.choice(all_news)

    title_az = translate_to_az(news["title"])
    summary_az = translate_to_az(news["summary"][:400])

    explanation = f"""
📰 **{title_az}**

📌 **Xülasə:**  
{summary_az}...

🔗 Ətraflı oxu: {news['link']}
"""

    return explanation


# ============================
#  Menyular
# ============================

main_menu = ReplyKeyboardMarkup(
    [
        ["📊 Büdcə və xərclər", "💰 Kalkulyatorlar"],
        ["🎓 Maliyyə dərsləri", "🧠 Şəxsi tövsiyələr"],
        ["📰 Xəbərlər", "🏦 Bank təklifləri"],
        ["💬 Sual ver (AI)", "🤖 AI rejimi"]
    ],
    resize_keyboard=True
)

mode_menu = ReplyKeyboardMarkup(
    [
        ["Kredit", "Depozit"],
        ["Büdcə", "Xəbər"],
        ["Sadə izah"],
        ["⬅️ Geri"]
    ],
    resize_keyboard=True
)

news_menu = ReplyKeyboardMarkup(
    [
        ["📈 Valyuta xəbərləri"],
        ["🏦 Bank sektoru xəbərləri"],
        ["📉 İqtisadi göstəricilər"],
        ["🌍 Dünya maliyyə xəbərləri"],
        ["⬅️ Geri"]
    ],
    resize_keyboard=True
)


# ============================
#  /start
# ============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Salam! Mən sənin maliyyə köməkçinəm.",
        reply_markup=main_menu
    )


# ============================
#  Əsas handler
# ============================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lower = text.lower()

    # -------------------------
    # AI REJIM MENYUSU
    # -------------------------

    if text == "🤖 AI rejimi":
        await update.message.reply_text("Rejim seç:", reply_markup=mode_menu)
        return

    if lower == "kredit":
        context.user_data["mode"] = "kredit"
        await update.message.reply_text("Rejim: Kredit eksperti")
        return

    if lower == "depozit":
        context.user_data["mode"] = "depozit"
        await update.message.reply_text("Rejim: Depozit eksperti")
        return

    if lower in ["büdcə", "budce"]:
        context.user_data["mode"] = "budce"
        await update.message.reply_text("Rejim: Büdcə planlayıcısı")
        return

    if lower == "xəbər":
        context.user_data["mode"] = "xeber"
        await update.message.reply_text("Rejim: Xəbər analitiki")
        return

    if lower == "sadə izah":
        context.user_data["mode"] = "sade"
        await update.message.reply_text("Rejim: Sadə izah")
        return

    # -------------------------
    # AI CHAT
    # -------------------------

    if text == "💬 Sual ver (AI)":
        context.user_data["state"] = "ai_chat"
        await update.message.reply_text("Sualını yaz:")
        return

    if context.user_data.get("state") == "ai_chat":
        mode = context.user_data.get("mode")
        prompt = build_prompt(text, mode)
        await update.message.reply_text("Fikirləşirəm...")

        answer = ask_ai(prompt)
        await update.message.reply_text(answer)
        return

    # -------------------------
    # XƏBƏRLƏR
    # -------------------------

    if text == "📰 Xəbərlər":
        await update.message.reply_text("Kateqoriya seç:", reply_markup=news_menu)
        return

    if text == "📈 Valyuta xəbərləri":
        msg = await get_dynamic_news("valyuta")
        await update.message.reply_text(msg)
        return

    if text == "🏦 Bank sektoru xəbərləri":
        msg = await get_dynamic_news("bank")
        await update.message.reply_text(msg)
        return

    if text == "📉 İqtisadi göstəricilər":
        msg = await get_dynamic_news("iqtisadiyyat")
        await update.message.reply_text(msg)
        return

    if text == "🌍 Dünya maliyyə xəbərləri":
        msg = await get_dynamic_news("dunya")
        await update.message.reply_text(msg)
        return

    # -------------------------
    # GERI
    # -------------------------

    if text == "⬅️ Geri":
        context.user_data.clear()
        await update.message.reply_text("Əsas menyu:", reply_markup=main_menu)
        return

    # -------------------------
    # DEFAULT
    # -------------------------

    await update.message.reply_text("Menyudan seçim et.")


# ============================
#  RUN
# ============================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot işə düşdü...")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app.run_polling()


if __name__ == "__main__":
    main()
