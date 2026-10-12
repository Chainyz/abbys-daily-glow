# Abby's Daily Glow Discord Bot

A Python Discord bot that rotates through the included selfies and posts a personalised confidence quote for Abby every day at 15:30 UK local time.

## Setup
1. Install Python 3.10+.
2. Create a Discord application at https://discord.com/developers/applications, add a bot, and invite it to your server with View Channel, Send Messages, and Attach Files permissions.
3. Copy `.env.example` to `.env`; fill in `DISCORD_TOKEN` and `CHANNEL_ID`. Keep `.env` private.
4. Install dependencies: `python -m pip install -r requirements.txt`
5. Run: `python bot.py`

## Schedule
`POST_TIME=15:30` means 3:30 PM UK civil time. The `Europe/London` timezone automatically follows GMT/BST daylight-saving changes. If you mean fixed GMT year-round, change `TIMEZONE` in `bot.py` to `ZoneInfo("Etc/GMT")` (note the reversed sign convention in IANA Etc zones is irrelevant for GMT zero).

## Selfies and rotation
Put images in `selfies/`. Supported: JPG, JPEG, PNG, GIF, WEBP. The bot uses alphabetical filename order and stores progress in `rotation.json`. Keep that file on persistent storage if hosting online.

## Test
To test, temporarily change `POST_TIME` to a few minutes in the future and restart the bot. The bot does not post immediately at startup.

## Safety
Never share your bot token. If exposed, reset it in the Discord Developer Portal. Do not commit `.env` or the private `rotation.json` file to a public repository.
