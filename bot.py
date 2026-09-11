import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

WELCOME = """<b>🇺🇸 Welcome to One American News</b>\n\nGet concise news summaries and general information about important stories from the United States and around the world.\n\n<b>What you can do here:</b>\n📰 Browse the latest news categories\n🇺🇸 Explore U.S. news topics\n🌎 Read world news summaries\nℹ️ Learn how the bot works\n\nSelect an option below to get started."""

ABOUT = """<b>ℹ️ About One American News</b>\n\nOne American News is an informational Telegram bot designed to organize concise news summaries by topic.\n\nThe bot provides a simple way to browse U.S. and international news categories without unnecessary clutter.\n\n<i>News summaries are provided for general informational purposes.</i>"""

CATEGORIES = """<b>📂 News Categories</b>\n\nChoose a category to view sample updates or connect the bot to your preferred news source later."""


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📰 Latest News", callback_data="latest"),
        InlineKeyboardButton(text="🇺🇸 U.S. News", callback_data="us_news"),
    )
    builder.row(
        InlineKeyboardButton(text="🌎 World News", callback_data="world_news"),
    )
    builder.row(
        InlineKeyboardButton(text="📂 Categories", callback_data="categories"),
        InlineKeyboardButton(text="ℹ️ About", callback_data="about"),
    )
    return builder.as_markup()


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Main Menu", callback_data="home")]]
    )


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(WELCOME, reply_markup=main_menu())


@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "<b>Help</b>\n\nUse the buttons below to browse news categories and learn more about One American News.",
        reply_markup=main_menu(),
    )


@dp.callback_query(F.data == "home")
async def home_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(WELCOME, reply_markup=main_menu())
    await callback.answer()


@dp.callback_query(F.data == "latest")
async def latest_handler(callback: CallbackQuery) -> None:
    text = (
        "<b>📰 Latest News</b>\n\n"
        "This section is ready to display current news summaries once a trusted news feed is connected.\n\n"
        "<i>No live stories are displayed in this starter version.</i>"
    )
    await callback.message.edit_text(text, reply_markup=back_menu())
    await callback.answer()


@dp.callback_query(F.data == "us_news")
async def us_news_handler(callback: CallbackQuery) -> None:
    text = (
        "<b>🇺🇸 U.S. News</b>\n\n"
        "Browse summaries about important events and developments in the United States.\n\n"
        "Connect a verified news source to populate this section with live stories."
    )
    await callback.message.edit_text(text, reply_markup=back_menu())
    await callback.answer()


@dp.callback_query(F.data == "world_news")
async def world_news_handler(callback: CallbackQuery) -> None:
    text = (
        "<b>🌎 World News</b>\n\n"
        "Explore international news and major global developments in a concise format.\n\n"
        "Connect a verified news source to populate this section with live stories."
    )
    await callback.message.edit_text(text, reply_markup=back_menu())
    await callback.answer()


@dp.callback_query(F.data == "categories")
async def categories_handler(callback: CallbackQuery) -> None:
    builder = InlineKeyboardBuilder()
    for label, value in [
        ("💻 Technology", "topic_technology"),
        ("💼 Business", "topic_business"),
        ("🔬 Science", "topic_science"),
        ("🏛️ Politics & Public Affairs", "topic_public_affairs"),
    ]:
        builder.row(InlineKeyboardButton(text=label, callback_data=value))
    builder.row(InlineKeyboardButton(text="🔙 Main Menu", callback_data="home"))
    await callback.message.edit_text(CATEGORIES, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "about")
async def about_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(ABOUT, reply_markup=back_menu())
    await callback.answer()


@dp.callback_query(F.data.startswith("topic_"))
async def topic_handler(callback: CallbackQuery) -> None:
    topic = callback.data.removeprefix("topic_").replace("_", " ").title()
    text = (
        f"<b>📌 {topic}</b>\n\n"
        "This category is ready for curated news summaries. "
        "Connect your selected news API or RSS sources to publish current stories here."
    )
    await callback.message.edit_text(text, reply_markup=back_menu())
    await callback.answer()


async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
