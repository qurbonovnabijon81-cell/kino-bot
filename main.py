import os
import logging
import aiosqlite
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [7642515423]

CHANNEL_ID = -1003105328904
CHANNEL_LINK = "https://t.me/CINEMAX121"

DB_PATH = "/data/movies.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_state = {}
last_video = {}

# ================= CHECK SUB =================

async def check_sub(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        ]
    except:
        return False

# ================= DB =================

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:

        # MOVIES
        await db.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            code TEXT UNIQUE,
            file_id TEXT,
            rating REAL,
            year INTEGER
        )
        """)

        # SERIALS
        await db.execute("""
        CREATE TABLE IF NOT EXISTS serials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            code TEXT,
            part INTEGER,
            file_id TEXT
        )
        """)

        await db.commit()

# ================= ADMIN CHECK =================

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ================= START =================

@dp.message(Command("start"))
async def start(message: types.Message):

    if not await check_sub(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanal", url=CHANNEL_LINK)]
        ])
        await message.answer("❗ Obuna bo‘ling", reply_markup=kb)
        return

    if is_admin(message.from_user.id):
        await message.answer("👑 Admin panel tayyor")
    else:
        await message.answer("🔍 Kino yoki serial kodini yozing")

# ================= VIDEO =================

@dp.message(lambda m: m.video)
async def video(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    last_video[message.from_user.id] = message.video.file_id
    await message.answer("✅ Video qabul qilindi")

# ================= ADD SERIAL =================

@dp.message(Command("serial"))
async def add_serial(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    user_state[message.from_user.id] = {"step": "s_name"}
    await message.answer("📺 Serial nomi:")

# ================= SERIAL STEPS =================

@dp.message()
async def steps(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    if message.from_user.id not in user_state:
        return

    state = user_state[message.from_user.id]

    # MOVIE LOGIC (old saqlanadi)
    if state.get("step") == "name":
        state["name"] = message.text
        state["step"] = "code"
        await message.answer("🔑 Kod:")

    elif state.get("step") == "code":
        state["code"] = message.text
        state["step"] = "rating"
        await message.answer("⭐ Reyting:")

    elif state.get("step") == "rating":
        state["rating"] = float(message.text)
        state["step"] = "year"
        await message.answer("📅 Yil:")

    elif state.get("step") == "year":
        state["year"] = int(message.text)

        file_id = last_video.get(message.from_user.id)
        if not file_id:
            await message.answer("❌ Video yo‘q")
            return

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO movies (name, code, file_id, rating, year) VALUES (?, ?, ?, ?, ?)",
                (state["name"], state["code"], file_id, state["rating"], state["year"])
            )
            await db.commit()

        await message.answer("✅ Kino saqlandi")
        user_state.pop(message.from_user.id)

    # ================= SERIAL =================
    elif state.get("step") == "s_name":
        state["name"] = message.text
        state["step"] = "s_code"
        await message.answer("🔑 Serial kod:")

    elif state.get("step") == "s_code":
        state["code"] = message.text
        state["step"] = "s_part"
        await message.answer("📺 Qism raqami:")

    elif state.get("step") == "s_part":
        state["part"] = int(message.text)

        file_id = last_video.get(message.from_user.id)
        if not file_id:
            await message.answer("❌ Video yo‘q")
            return

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO serials (name, code, part, file_id) VALUES (?, ?, ?, ?)",
                (state["name"], state["code"], state["part"], file_id)
            )
            await db.commit()

        await message.answer("✅ Serial saqlandi")
        user_state.pop(message.from_user.id)

# ================= SEARCH =================

@dp.message()
async def search(message: types.Message):

    text = message.text.lower()

    async with aiosqlite.connect(DB_PATH) as db:

        # MOVIE
        async with db.execute(
            "SELECT name, file_id, rating, year FROM movies WHERE code=? OR name LIKE ?",
            (text, f"%{text}%")
        ) as c:
            movie = await c.fetchone()

        # SERIAL
        async with db.execute(
            "SELECT name, part, file_id FROM serials WHERE code=?",
            (text,)
        ) as c:
            serial = await c.fetchall()

    if movie:
        name, file_id, rating, year = movie
        await message.answer_video(
            video=file_id,
            caption=f"🎬 {name}\n⭐ {rating} | 📅 {year}"
        )
        return

    if serial:
        for name, part, file_id in serial:
            await message.answer_video(
                video=file_id,
                caption=f"📺 {name} | 🎞 {part}-qism"
            )
        return

    await message.answer("❌ Topilmadi")

# ================= 📊 ADMIN STATISTICS =================

@dp.message(Command("stats"))
async def stats(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    async with aiosqlite.connect(DB_PATH) as db:

        movies = await db.execute("SELECT COUNT(*) FROM movies")
        movies = (await movies.fetchone())[0]

        serials = await db.execute("SELECT COUNT(*) FROM serials")
        serials = (await serials.fetchone())[0]

    await message.answer(
        f"📊 STATISTIKA:\n\n"
        f"🎬 Kinolar: {movies}\n"
        f"📺 Seriallar: {serials}"
    )

# ================= WEBHOOK =================

WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "secret123"

async def on_startup(app):
    await init_db()
    url = os.getenv("RENDER_EXTERNAL_URL")
    await bot.set_webhook(f"{url}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)

async def on_shutdown(app):
    await bot.delete_webhook()

def main():
    app = web.Application()

    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET
    ).register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()