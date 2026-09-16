# One American News

A simple Telegram-native news bot with exactly three user-facing functions:

- Latest News
- U.S. News
- World News

## Requirements

- Python 3.12+
- Telegram bot token

## Environment

Set:

`BOT_TOKEN=your_telegram_bot_token_here`

Optional:

`LOG_LEVEL=INFO`

## Run locally

```bash
pip install -r requirements.txt
python bot.py
```

## Docker

```bash
docker build -t onenews .
docker run --rm -e BOT_TOKEN=your_token onenews
```

The bot uses public RSS feeds and does not require a news API key or database.

## Supported commands

- /start
- /help

## User flow

/start → choose one of the three news sections → receive current headlines → open the original source or refresh → return to Main Menu.

If a feed is temporarily unavailable, the bot displays a retry path instead of exposing an exception or leaving the user stuck.
