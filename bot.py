import asyncio
import html
import logging
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import quote

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("onenews")

BOT_TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()

@dataclass(frozen=True)
class Story:
    title: str
    link: str
    source: str

FEEDS = {
    "latest": (
        ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ),
    "us": (
        ("BBC U.S. & Canada", "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml"),
        ("Google News U.S.", "https://news.google.com/rss/search?q=United+States&hl=en-US&gl=US&ceid=US:en"),
    ),
    "world": (
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ),
}

LABELS = {
    "latest": "📰 Latest News",
    "us": "🇺🇸 U.S. News",
    "world": "🌎 World News",
}

WELCOME = (
    "<b>🇺🇸 Welcome to One American News</b>\n\n"
    "Browse current news in three simple sections. "
    "Choose a section below to load recent headlines directly in Telegram."
)

HELP = (
    "<b>Help</b>\n\n"
    "Use the three buttons to browse recent headlines:\n"
    "📰 Latest News — current top stories\n"
    "🇺🇸 U.S. News — recent U.S. stories\n"
    "🌎 World News — recent international stories\n\n"
    "Tap a headline to open the original source, or use Main Menu to return."
)

async def fetch_feed(session: aiohttp.ClientSession, source: str, url: str) -> list[Story]:
    async with session.get(
        url,
        timeout=aiohttp.ClientTimeout(total=8),
        headers={"User-Agent": "OneAmericanNews/1.0"},
    ) as response:
        response.raise_for_status()
        payload = await response.read()

    root = ET.fromstring(payload)
    stories: list[Story] = []

    for item in root.iter():
        if item.tag.lower().endswith("item"):
            title = ""
            link = ""
            for child in item:
                tag = child.tag.lower()
                if tag.endswith("title") and not title:
                    title = (child.text or "").strip()
                elif tag.endswith("link") and not link:
                    link = (child.text or "").strip()

            title = re.sub(r"\s+", " ", html.unescape(title)).strip()
            if title and link.startswith(("http://", "https://")):
                stories.append(Story(title=title, link=link, source=source))
            if len(stories) >= 5:
                break

    return stories

async def get_stories(category: str) -> list[Story]:
    feeds = FEEDS[category]
    async with aiohttp.ClientSession() as session:
        for source, url in feeds:
            try:
                stories = await fetch_feed(session, source, url)
                if stories:
                    return stories
            except (aiohttp.ClientError, asyncio.TimeoutError, ET.ParseError) as exc:
                logger.warning("News feed failed: %s | %s", source, exc)
            except Exception:
                logger.exception("Unexpected feed error: %s", source)
    return []

def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📰 Latest News", callback_data="news:latest"),
    )
    builder.row(
        InlineKeyboardButton(text="🇺🇸 U.S. News", callback_data="news:us"),
    )
    builder.row(
        InlineKeyboardButton(text="🌎 World News", callback_data="news:world"),
    )
    return builder.as_markup()

def news_menu(category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Refresh", callback_data=f"news:{category}"),
        InlineKeyboardButton(text="🏠 Main Menu", callback_data="home"),
    )
    return builder.as_markup()

def story_menu(stories: list[Story], category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, story in enumerate(stories):
        builder.row(
            InlineKeyboardButton(
                text=f"{index + 1}. {story.title[:55]}",
                url=story.link,
            )
        )
    builder.row(
        InlineKeyboardButton(text="🔄 Refresh", callback_data=f"news:{category}"),
        InlineKeyboardButton(text="🏠 Main Menu", callback_data="home"),
    )
    return builder.as_markup()

def format_stories(category: str, stories: list[Story]) -> str:
    lines = [f"<b>{LABELS[category]}</b>", "", "Recent headlines:"]
    for index, story in enumerate(stories, start=1):
        lines.append(f"<b>{index}.</b> {html.escape(story.title)}")
        lines.append(f"<i>Source: {html.escape(story.source)}</i>")
    return "\n".join(lines)

async def show_news(target: Message | CallbackQuery, category: str) -> None:
    if isinstance(target, CallbackQuery):
        message = target.message
    else:
        message = target

    if message is None:
        return

    stories = await get_stories(category)
    if stories:
        text = format_stories(category, stories)
        markup = story_menu(stories, category)
    else:
        text = (
            f"<b>{LABELS[category]}</b>\n\n"
            "The news source is temporarily unavailable. "
            "Please try again in a moment."
        )
        markup = news_menu(category)

    try:
        if isinstance(target, CallbackQuery):
            await message.edit_text(text, reply_markup=markup)
        else:
            await message.answer(text, reply_markup=markup)
    except TelegramBadRequest:
        logger.info("Telegram rejected an unchanged message update")

@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    # Telegram Ads may append a start parameter; CommandStart safely accepts it.
    await message.answer(WELCOME, reply_markup=main_menu())

@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(HELP, reply_markup=main_menu())

@dp.callback_query(F.data == "home")
async def home_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(WELCOME, reply_markup=main_menu())

@dp.callback_query(F.data.startswith("news:"))
async def news_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    category = callback.data.split(":", 1)[1]
    if category not in FEEDS:
        if callback.message:
            await callback.message.edit_text(
                "That section is unavailable. Please return to the main menu.",
                reply_markup=main_menu(),
            )
        return
    await show_news(callback, category)

async def on_startup(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Open the main menu"),
            BotCommand(command="help", description="How to use One American News"),
        ]
    )
    logger.info("One American News started")

async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is required")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await bot.delete_webhook(drop_pending_updates=True)
    await on_startup(bot)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
