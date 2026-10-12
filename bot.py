import json
import logging
import os
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
POST_TIME = os.getenv("POST_TIME", "15:30")
TEST_POST_NOW = os.getenv("TEST_POST_NOW", "").lower() == "true"

# UK civil time: automatically follows GMT/BST changes.
TIMEZONE = ZoneInfo("Europe/London")
BASE_DIR = Path(__file__).resolve().parent
SELFIES_DIR = BASE_DIR / "selfies"
STATE_FILE = BASE_DIR / "rotation.json"

try:
    hour, minute = map(int, POST_TIME.split(":"))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError
    SCHEDULE_TIME = time(hour, minute, tzinfo=TIMEZONE)
except ValueError:
    raise SystemExit("POST_TIME must be a valid 24-hour time, e.g. 15:30")

if not TOKEN or CHANNEL_ID == 0:
    raise SystemExit("Set DISCORD_TOKEN and CHANNEL_ID in Railway Variables.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

QUOTES = [
    "Abby, never forget how stunning you are — not just in the way you look, but in the kindness, courage, and light you bring into the world. ✨ I love you bubba",
    "Abby, you are powerful, beautiful, and more capable than your doubts will ever admit. Take up space and let yourself shine. 👑 I love you bubbie",
    "To the incredible Abby: you make the world brighter simply by being yourself. Never shrink your light to make it easier for others to see. ☀️ I love you bubs",
    "Abby, your beauty catches the eye, but your heart, strength, and spirit are what make you unforgettable. 💖 I love you baby",
    "A reminder for Abby: you don't need to prove your worth today. You are already enough, exactly as you are — and you are extraordinary. 🌷 I love you pumpkin",
    "Abby, walk into today with your head held high. You have a beautiful soul, a powerful spirit, and every right to believe in yourself. 🔥 I love you bubba",
    "The world is lucky to have you in it, Abby. Keep being brave, keep being kind, and never forget how much good you bring. 🌟 I love you bubbie",
    "Abby, you are not meant to fade into the background. Your voice matters, your dreams matter, and your presence matters. 💫 I love you bubs",
    "Beautiful Abby, give yourself the same love and encouragement you so freely give to others. You deserve that gentleness, too. 🤍 I love you baby",
    "Abby, you can be a work in progress and still be absolutely wonderful. Every step you take is part of your strength. 🌱 I love you pumpkin",
    "Abby, your confidence doesn't have to be loud to be powerful. Trust yourself, honour your boundaries, and own your magic. 💎 I love you bubba",
    "For Abby: may you see yourself today with kinder eyes — strong, stunning, resilient, and full of possibilities. 💐 I love you bubbie",
    "Abby, you have survived days you thought would defeat you. Let that remind you of the strength you carry into every new beginning. 💪 I love you bubs",
    "Abby, you deserve to chase the life that excites you, celebrate your wins, and feel proud of the person you are becoming. 🚀 I love you baby",
    "Hey Abby, the combination of your beauty, warmth, and individuality is your own. No one else can be you — and that's your superpower. 🦋 I love you pumpkin",
    "Abby, let today be another chance to stand tall, believe in your abilities, and remember that you are deeply appreciated. 🌈 I love you bubba",
    "A little truth for Abby: you don't have to be perfect to be breathtakingly special. Being authentically you is more than enough. ✨ I love you bubbie",
    "Abby, protect your peace, follow what makes your heart feel alive, and never apologise for growing into your strongest self. 🌻 I love you bubs",
    "To my reminder-worthy Abby: you are a whole universe of potential, humour, tenderness, and strength. Keep discovering all you can be. 🌌 I love you baby",
    "Abby, you are one of a kind. Let your smile be real, your boundaries be firm, and your dreams be bigger than your fears. 👑 I love you pumpkin",
    "Abby, I hope you remember today that you are loved, valued, and capable of more than you give yourself credit for. 💛 I love you bubba",
    "Stunning Abby, don't wait for someone else to tell you you're extraordinary. Look at how far you've come and give yourself that credit. 🥇 I love you bubbie",
    "Abby, the planet has billions of people, but there is only one you. Your mix of heart, strength, and sparkle is irreplaceable. 🌍 I love you bubs",
    "Abby, make today yours: take the chance, celebrate the small wins, and carry yourself like someone who knows she belongs. 💫 I love you baby",
    "Beautiful Abby, you deserve a life where you feel safe to be yourself, proud of your progress, and excited about what's next. 🌸 I love you pumpkin",
    "Abby, even on the days when confidence feels far away, your worth stays exactly the same. You are still wonderful. 🤍 I love you bubba",
    "Abby, your softness is not weakness and your strength doesn't make you any less gentle. You can be both, beautifully. 🌷 I love you bubbie",
    "To the most incredible Abby: thank you for being you. The world is better with your particular kind of light in it. ☀️ I love you bubs",
    "Abby, let your standards be high, your self-talk be kind, and your belief in your future be stronger than your fear. 🔥 I love you baby",
    "Abby, you are allowed to take up room, change your mind, start again, and become everything you've been dreaming of. 🌟 I love you pumpkin",
]


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"image_index": 0, "quote_index": 0}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


async def post_daily():
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    # Use the selfies folder when present. Also support photos beside bot.py,
    # so the bot still works if the repository layout changes.
    image_folder = SELFIES_DIR if SELFIES_DIR.exists() else BASE_DIR
    images = sorted(
        p for p in image_folder.iterdir()
        if p.is_file()
        and p.suffix.lower() in image_extensions
        and p.name.lower().startswith("selfie_")
    )

    if not images:
        logging.error("No selfie images found in the selfies folder or beside bot.py.")
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        channel = await bot.fetch_channel(CHANNEL_ID)

    state = load_state()
    image_index = state.get("image_index", 0) % len(images)
    quote_index = state.get("quote_index", 0) % len(QUOTES)
    photo = images[image_index]
    quote = QUOTES[quote_index]

    # Photo is deliberately sent first so the quote appears below it.
    await channel.send(
        content="✨ **A DAILY REMINDER FOR ABBY** ✨",
        file=discord.File(photo, filename=photo.name),
        allowed_mentions=discord.AllowedMentions.none(),
    )
    await channel.send(
        f"> 💖 {quote}\n\n"
        "**Keep glowing. Keep growing. Keep being wonderfully you.** ✨",
        allowed_mentions=discord.AllowedMentions.none(),
    )

    state["image_index"] = image_index + 1
    state["quote_index"] = (quote_index + 1) % len(QUOTES)
    save_state(state)
    logging.info("Posted %s and quote %d.", photo.name, quote_index + 1)


@tasks.loop(time=SCHEDULE_TIME)
async def daily_post():
    try:
        await post_daily()
    except Exception:
        logging.exception("Daily post failed.")


@daily_post.before_loop
async def before_daily_post():
    await bot.wait_until_ready()


@daily_post.error
async def daily_post_error(error):
    logging.error("Scheduler error: %s", error)


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    logging.info("Logged in as %s", bot.user)
    logging.info("Daily post scheduled for %s Europe/London time.", POST_TIME)

    if TEST_POST_NOW:
        try:
            await post_daily()
            logging.info(
                "One-time test post completed. Remove TEST_POST_NOW from Railway Variables now."
            )
        except Exception:
            logging.exception("One-time test post failed.")

    if not daily_post.is_running():
        daily_post.start()


bot.run(TOKEN)
