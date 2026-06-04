from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import math
import feedparser
import random
import requests

TOKEN = "8858168859:AAFTZq0rUVWgYWCepmmozFL_Z5vAPq-EUCM"

# ============================
#  AI (мини‑ChatGPT)
# ============================

DEEPSEEK_API_KEY = "sk-644844094ef541c1898247f6e55c9e4c"

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
                {"role": "system", "content": "Sən Azərbaycan dilində danışan maliyyə köməkçisisən. Cavabları sadə, aydın və konkret ver."},
                {"role": "user", "content": prompt}
            ],
            "thinking": {"type": "enabled"},
            "reasoning_effort": "high",
            "stream": False
        }

        r = requests.post(url, json=data, headers=headers, timeout=30)
        r.raise_for_status()
        resp = r.json()

        # DeepSeek возвращает ответ так:
        # resp["choices"][0]["message"]["content"]
        return resp["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("DEEPSEEK ERROR:", e)
        return "AI cavabında problem yarandı. Bir az sonra yenidən cəhd et."


# ============================
#  Tərcümə funksiyası (AZ)
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

📘 **Bu xəbər nə deməkdir?**  
Bu xəbər iqtisadi və maliyyə bazarlarında müəyyən dəyişikliklərə işarə edir.

🎯 **Kimə təsir edir?**  
• Bank müştərilərinə  
• Kredit və depozit sahiblərinə  
• Sahibkarlara  
• İnvestorlara  

💡 **Niyə vacibdir?**  
Çünki bu cür xəbərlər faizlərə, valyutaya və bank xidmətlərinə təsir edir.

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
        ["💬 Sual ver (AI)"]   # ← ДОБАВИЛ КНОПКУ
    ],
    resize_keyboard=True
)

calc_menu = ReplyKeyboardMarkup(
    [
        ["📈 Depozit kalkulyatoru"],
        ["💳 Kredit kalkulyatoru"],
        ["🎯 Yığım kalkulyatoru"],
        ["⬅️ Geri"]
    ],
    resize_keyboard=True
)

lessons_menu = ReplyKeyboardMarkup(
    [
        ["📘 Büdcə nədir?"],
        ["💳 Kreditlər necə işləyir?"],
        ["💰 Depozit və faizlər"],
        ["📈 İnvestisiya əsasları"],
        ["🧠 Maliyyə davranışı"],
        ["⬅️ Geri"]
    ],
    resize_keyboard=True
)

bank_menu = ReplyKeyboardMarkup(
    [
        ["💰 Ən yaxşı depozitlər"],
        ["💳 Ən yaxşı kreditlər"],
        ["💳 Kartlar və keşbek"],
        ["🏦 Bank müqayisəsi"],
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
        ["🔄 Xəbərləri yenilə"],
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

    # -------------------------
    # AI CHAT MODE
    # -------------------------
    if text == "💬 Sual ver (AI)":
        context.user_data["state"] = "ai_chat"
        await update.message.reply_text("Sualını yaz, mən cavab verim:")
        return

    if context.user_data.get("state") == "ai_chat":
        question = text
        await update.message.reply_text("Fikirləşirəm...")

        answer = ask_ai(question)
        await update.message.reply_text(answer)
        return

    # -------------------------
    # Xəbərlər
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

    if text == "🔄 Xəbərləri yenilə":
        msg = await get_dynamic_news("iqtisadiyyat")
        await update.message.reply_text(msg)
        return

    # -------------------------
    # Geri
    # -------------------------

    if text == "⬅️ Geri":
        context.user_data.clear()
        await update.message.reply_text("Əsas menyu:", reply_markup=main_menu)
        return

    # -------------------------
    # Default
    # -------------------------

    await update.message.reply_text("Menyudan seçim et.")


# ============================
#  Run
# ============================

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot işə düşdü...")
    app.run_polling()

if __name__ == "__main__":
    main()
