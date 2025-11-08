import os
import httpx
import json
from dotenv import load_dotenv
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

dotenv_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📰 Tech News", callback_data='tech')],
        [InlineKeyboardButton("💹 Stock Market", callback_data='stocks')],
        [InlineKeyboardButton("🤖 AI Updates", callback_data='ai')],
        [InlineKeyboardButton("🪙 Crypto", callback_data='crypto')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton("⬅️ Back to Categories", callback_data='start')]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *NewsPulse Bot!*\n\n"
        "Choose a category below or simply **type any topic** (like 'NVIDIA' or 'Tesla') to search for news.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

async def get_news(topic: str) -> str:
    query_map = {
        'stocks': 'stock market',
        'ai': 'artificial intelligence',
        'crypto': 'cryptocurrency',
        'tech': 'technology'
    }
    query = query_map.get(topic, topic)

    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except (httpx.RequestError, json.JSONDecodeError) as e:
        print(f"Error fetching news for query '{query}': {e}")
        return "⚠️ Sorry, I couldn't fetch the news right now. Please try again later."

    articles = data.get("articles", [])[:5]

    if not articles:
        return f"⚠️ No recent articles found for '{query}'."

    text = ""
    for article in articles:
        title = article.get("title", "No title")
        url = article.get("url", "")
        description = article.get("description", "No description available.")
        source = article.get("source", {}).get("name", "Unknown Source")

        if not title: title = "No title"
        if not description: description = "No description available."
        if not source: source = "Unknown Source"

        title = title.replace("[", "\\[").replace("]", "\\]").replace("_", "\\_").replace("*", "\\*")
        description = description.replace("[", "\\[").replace("]", "\\]").replace("_", "\\_").replace("*", "\\*")
        source = source.replace("[", "\\[").replace("]", "\\]").replace("_", "\\_").replace("*", "\\*")

        text += f"• *[{title}]({url})*\n"
        text += f"  `{description}`\n"
        text += f"  *Source:* {source}\n\n"

    return text

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    topic = query.data
    topic_title = topic.capitalize()

    if topic == 'start':
        await query.edit_message_text(
            "👋 Welcome back! Choose a category or type a topic to search 👇",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
        return

    await query.edit_message_text(f"⏳ Fetching latest *{topic_title}* news...")
    news_message = await get_news(topic)

    await query.edit_message_text(
        f"🗞 *Latest {topic_title} News:*\n\n{news_message}",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def search_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search_query = update.message.text
    topic_title = search_query.capitalize()

    await update.message.reply_text(f"⏳ Searching for news about *{topic_title}*...", parse_mode="Markdown")
    news_message = await get_news(search_query)

    await update.message.reply_text(
        f"🗞 *Search Results for {topic_title}:*\n\n{news_message}",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN variable is empty. Check your .env file.")
        return
    if not NEWS_API_KEY:
        print("Error: NEWS_API_KEY variable is empty. Check your .env file.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_query))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), search_news))

    print("🤖 NewsPulse Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()