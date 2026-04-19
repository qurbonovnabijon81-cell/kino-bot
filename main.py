import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
import os
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7642515423  # O'z IDngizni qo'ying

CHANNEL_ID = -1003105328904 # Kanal ID'si
CHANNEL_LINK = "https://t.me/CINEMAX121"

bot = Bot(token=TOKEN)
dp = Dispatcher()

last_video = {}

# MENU
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Kinolar"), KeyboardButton(text="📺 Seriallar")],
        [KeyboardButton(text="🔍 Qidirish"), KeyboardButton(text="🎭 Kategoriyalar")],
        [KeyboardButton(text="⭐ Top kinolar"), KeyboardButton(text="📊 Statistika")]
    ],
    resize_keyboard=True
)

# Kategoriya menyusi
category_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎭 Janr", callback_data="cat_genre"),
     InlineKeyboardButton(text="📅 Yil", callback_data="cat_year")],
    [InlineKeyboardButton(text="⭐ Reyting", callback_data="cat_rating"),
     InlineKeyboardButton(text="⏱ Davomiylik", callback_data="cat_duration")],
    [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu")]
])

# Janrlar
genres = {
    "action": "🎬 JANGARI",
    "comedy": "😄 KOMEDIYA",
    "drama": "🎭 DRAMA",
    "horror": "👻 QO'RQINCHI",
    "fantasy": "✨ FANTASY",
    "thriller": "🔪 TRILLER",
    "romance": "💖 ROMANTIK",
    "crime": "🚔 JINOYAT"
}

# DATABASE
async def init_db():
    async with aiosqlite.connect("movies.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            code TEXT,
            file_id TEXT,
            image TEXT,
            genre TEXT,
            year INTEGER,
            rating REAL,
            duration INTEGER
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS serials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            code TEXT,
            part INTEGER,
            file_id TEXT,
            genre TEXT,
            year INTEGER,
            rating REAL
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            join_date TEXT,
            total_views INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_id INTEGER,
            movie_type TEXT,
            view_date TEXT
        )
        """)

        await db.commit()

# OBUNA CHECK
async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except:
        return False

# STATISTIKA QO'SHISH
async def add_view(user_id, movie_name, movie_type):
    from datetime import datetime
    async with aiosqlite.connect("movies.db") as db:
        await db.execute(
            "INSERT INTO views (user_id, movie_id, movie_type, view_date) VALUES (?, ?, ?, ?)",
            (user_id, movie_name, movie_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        await db.execute(
            "UPDATE users SET total_views = total_views + 1 WHERE id = ?",
            (user_id,)
        )
        await db.commit()

# START COMMAND
@dp.message(Command("start"))
async def start_command(message: types.Message):
    from datetime import datetime

    async with aiosqlite.connect("movies.db") as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (id, username, first_name, join_date) VALUES (?, ?, ?, ?)",
            (
                message.from_user.id,
                message.from_user.username,
                message.from_user.first_name,
                datetime.now().strftime("%Y-%m-%d")
            )
        )
        await db.commit()

    await message.answer("👋 Xush kelibsiz!", reply_markup=menu)

# OBUNA TEKSHIRISH CALLBACK
@dp.callback_query(lambda c: c.data == "check_sub")
async def check_btn(callback: types.CallbackQuery):
    if await check_sub(callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer("✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.", reply_markup=menu)
    else:
        await callback.answer("❌ Kanalga obuna bo'ling!", show_alert=True)

# ADMIN COMMANDS
@dp.message(Command("save"))
async def save_movie(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        args = message.text.split(maxsplit=7)
        if len(args) != 8:
            await message.answer("❌ Format: /save nom kod rasm_url janr yil reyting davomiylik\n\n"
                               f"Janrlar: {', '.join(genres.keys())}\n"
                               "Misol: /save titanic tit123 rasm_url romance 1997 8.5 195")
            return
        
        _, name, code, image, genre, year, rating, duration = args
        file_id = last_video.get("file_id")
        
        if not file_id:
            await message.answer("❌ Avval video yuboring!")
            return
        
        if genre not in genres:
            await message.answer(f"❌ Noto'g'ri janr! Janrlar: {', '.join(genres.keys())}")
            return
        
        async with aiosqlite.connect("movies.db") as db:
            await db.execute(
                "INSERT INTO movies (name, code, file_id, image, genre, year, rating, duration) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name.lower(), code, file_id, image, genre, int(year), float(rating), int(duration))
            )
            await db.commit()
        
        await message.answer(f"✅ Kino saqlandi:\n"
                            f"🎬 Nomi: {name}\n"
                            f"🎭 Janr: {genres[genre]}\n"
                            f"📅 Yil: {year}\n"
                            f"⭐ Reyting: {rating}\n"
                            f"⏱ Davomiylik: {duration} daqiqa")
        last_video["file_id"] = None
        
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")

@dp.message(Command("serial"))
async def save_serial(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        args = message.text.split(maxsplit=6)
        if len(args) != 7:
            await message.answer("❌ Format: /serial nom kod qism janr yil reyting\n\n"
                               f"Janrlar: {', '.join(genres.keys())}\n"
                               "Misol: /serial breaking_bad brbad 1 drama 2008 9.5")
            return
        
        _, name, code, part, genre, year, rating = args
        file_id = last_video.get("file_id")
        
        if not file_id:
            await message.answer("❌ Avval video yuboring!")
            return
        
        if genre not in genres:
            await message.answer(f"❌ Noto'g'ri janr! Janrlar: {', '.join(genres.keys())}")
            return
        
        async with aiosqlite.connect("movies.db") as db:
            await db.execute(
                "INSERT INTO serials (name, code, part, file_id, genre, year, rating) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name.lower(), code, int(part), file_id, genre, int(year), float(rating))
            )
            await db.commit()
        
        await message.answer(f"✅ Serial saqlandi:\n"
f"📺 Nomi: {name}\n"
                            f"🎭 Janr: {genres[genre]}\n"
                            f"📅 Yil: {year}\n"
                            f"⭐ Reyting: {rating}\n"
                            f"📀 Qism: {part}")
        last_video["file_id"] = None
        
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")

# VIDEO QABUL (ADMIN)
@dp.message(lambda message: message.video and message.from_user.id == ADMIN_ID)
async def receive_video(message: types.Message):
    last_video["file_id"] = message.video.file_id
    await message.answer("✅ Video saqlandi!\n"
                        "Kino: /save nom kod rasm_url janr yil reyting davomiylik\n"
                        "Serial: /serial nom kod qism janr yil reyting")

# KATEGORIYA BO'YICHA FILTR
async def filter_by_category(message, category, value, is_movie=True):
    async with aiosqlite.connect("movies.db") as db:
        if is_movie:
            query = f"SELECT name, file_id, rating, year, duration FROM movies WHERE {category} {value} ORDER BY rating DESC LIMIT 20"
            async with db.execute(query) as cursor:
                items = await cursor.fetchall()
        else:
            query = f"SELECT DISTINCT name, code, rating, year FROM serials WHERE {category} {value} ORDER BY rating DESC LIMIT 20"
            async with db.execute(query) as cursor:
                items = await cursor.fetchall()
    
    if items:
        if is_movie:
            for name, file_id, rating, year, duration in items:
                await message.answer_video(
                    video=file_id,
                    caption=f"🎬 {name.title()}\n⭐ Reyting: {rating}\n📅 Yil: {year}\n⏱ {duration} daqiqa",
                    reply_markup=menu
                )
                await add_view(message.from_user.id, name, "movie")
        else:
            for name, code, rating, year in items:
                await message.answer(
                    f"📺 {name.title()}\n"
                    f"⭐ Reyting: {rating}\n"
                    f"📅 Yil: {year}\n"
                    f"🔑 Kod: {code}\n"
                    f"💡 Qidirish uchun kod yoki nomni yozing",
                    reply_markup=menu
                )
    else:
        await message.answer("❌ Hech narsa topilmadi", reply_markup=menu)

# KATEGORIYA CALLBACKLARI
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("🏠 Asosiy menyu", reply_markup=menu)

@dp.callback_query(lambda c: c.data == "cat_genre")
async def genre_filter(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    for i, (key, value) in enumerate(genres.items(), 1):
        row.append(InlineKeyboardButton(text=value, callback_data=f"genre_{key}"))
        if i % 2 == 0:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_cat")])
    
    await callback.message.edit_text("🎭 Janr tanlang:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("genre_"))
async def show_by_genre(callback: types.CallbackQuery):
    genre = callback.data.split("_")[1]
    await callback.message.delete()
    
    # Kinolar
    async with aiosqlite.connect("movies.db") as db:
        async with db.execute(
            "SELECT name, file_id, rating, year, duration FROM movies WHERE genre=? ORDER BY rating DESC LIMIT 10",
            (genre,)
        ) as cursor:
            movies = await cursor.fetchall()
    
    # Seriallar
    async with aiosqlite.connect("movies.db") as db:
        async with db.execute(
            "SELECT DISTINCT name, code, rating, year FROM serials WHERE genre=? ORDER BY rating DESC LIMIT 10",
            (genre,)
        ) as cursor:
             serials = await cursor.fetchall()
    
    if not movies and not serials:
        await callback.message.answer(f"❌ {genres[genre]} janrida hech narsa topilmadi", reply_markup=menu)
        return
    
    await callback.message.answer(f"🎭 {genres[genre]} janri:", reply_markup=menu)
    
    for name, file_id, rating, year, duration in movies:
        await callback.message.answer_video(
            video=file_id,
            caption=f"🎬 {name.title()}\n⭐ {rating} | 📅 {year} | ⏱ {duration} min",
            reply_markup=menu
        )
        await add_view(callback.from_user.id, name, "movie")
    
    for name, code, rating, year in serials:
        await callback.message.answer(
            f"📺 {name.title()}\n⭐ {rating} | 📅 {year}\n🔑 Kod: {code}",
            reply_markup=menu
        )

@dp.callback_query(lambda c: c.data == "cat_year")
async def year_filter(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="2020-2025", callback_data="year_new"),
         InlineKeyboardButton(text="2010-2019", callback_data="year_mid")],
        [InlineKeyboardButton(text="2000-2009", callback_data="year_old"),
         InlineKeyboardButton(text="1990-1999", callback_data="year_vintage")],
        [InlineKeyboardButton(text="1989 va undan eski", callback_data="year_classic")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_cat")]
    ])
    await callback.message.edit_text("📅 Yil oralig'ini tanlang:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("year_"))
async def show_by_year(callback: types.CallbackQuery):
    year_range = callback.data.split("_")[1]
    
    if year_range == "new":
        condition = "year BETWEEN 2020 AND 2025"
    elif year_range == "mid":
        condition = "year BETWEEN 2010 AND 2019"
    elif year_range == "old":
        condition = "year BETWEEN 2000 AND 2009"
    elif year_range == "vintage":
        condition = "year BETWEEN 1990 AND 1999"
    else:
        condition = "year <= 1989"
    
    await callback.message.delete()
    await filter_by_category(callback.message, condition, "", True)
    await filter_by_category(callback.message, condition, "", False)

@dp.callback_query(lambda c: c.data == "cat_rating")
async def rating_filter(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐⭐⭐⭐⭐ 9+", callback_data="rating_9")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐ 8-9", callback_data="rating_8")],
        [InlineKeyboardButton(text="⭐⭐⭐ 7-8", callback_data="rating_7")],
        [InlineKeyboardButton(text="⭐⭐ 6-7", callback_data="rating_6")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_cat")]
    ])
    await callback.message.edit_text("⭐ Reyting bo'yicha tanlang:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("rating_"))
async def show_by_rating(callback: types.CallbackQuery):
    rating = float(callback.data.split("_")[1])
    
    if rating == 9:
        condition = "rating >= 9"
    elif rating == 8:
        condition = "rating >= 8 AND rating < 9"
    elif rating == 7:
        condition = "rating >= 7 AND rating < 8"
    else:
        condition = "rating >= 6 AND rating < 7"
    
    await callback.message.delete()
    await filter_by_category(callback.message, condition, "", True)
    await filter_by_category(callback.message, condition, "", False)

@dp.callback_query(lambda c: c.data == "cat_duration")
async def duration_filter(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
[InlineKeyboardButton(text="⏱ Qisqa (< 90 min)", callback_data="dur_short")],
        [InlineKeyboardButton(text="⏱ O'rta (90-120 min)", callback_data="dur_medium")],
        [InlineKeyboardButton(text="⏱ Uzun (120-150 min)", callback_data="dur_long")],
        [InlineKeyboardButton(text="⏱ Juda uzun (> 150 min)", callback_data="dur_epic")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_cat")]
    ])
    await callback.message.edit_text("⏱ Davomiylik bo'yicha tanlang:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("dur_"))
async def show_by_duration(callback: types.CallbackQuery):
    dur_type = callback.data.split("_")[1]
    
    if dur_type == "short":
        condition = "duration < 90"
    elif dur_type == "medium":
        condition = "duration BETWEEN 90 AND 120"
    elif dur_type == "long":
        condition = "duration BETWEEN 120 AND 150"
    else:
        condition = "duration > 150"
    
    await callback.message.delete()
    await filter_by_category(callback.message, condition, "", True)

@dp.callback_query(lambda c: c.data == "back_to_cat")
async def back_to_categories(callback: types.CallbackQuery):
    await callback.message.edit_text("🎭 Kategoriyalar:", reply_markup=category_menu)

# TOP KINOLAR
@dp.message(lambda message: message.text == "⭐ Top kinolar")
async def top_movies(message: types.Message):
    if not await check_sub(message.from_user.id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
            ]
        )
        await message.answer("❗ Iltimos, botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=keyboard)
        return
    
    async with aiosqlite.connect("movies.db") as db:
        async with db.execute(
            "SELECT name, file_id, rating, year, duration FROM movies ORDER BY rating DESC LIMIT 10"
        ) as cursor:
            top_movies = await cursor.fetchall()
        
        async with db.execute(
            "SELECT name, code, rating, year FROM serials ORDER BY rating DESC LIMIT 10"
        ) as cursor:
            top_serials = await cursor.fetchall()
    
    if top_movies:
        await message.answer("⭐ TOP 10 KINOLAR:", reply_markup=menu)
        for name, file_id, rating, year, duration in top_movies:
            await message.answer_video(
                video=file_id,
                caption=f"🎬 {name.title()}\n⭐ {rating} | 📅 {year} | ⏱ {duration} min",
                reply_markup=menu
            )
            await add_view(message.from_user.id, name, "movie")
    
    if top_serials:
        await message.answer("⭐ TOP 10 SERIALLAR:", reply_markup=menu)
        for name, code, rating, year in top_serials:
            await message.answer(
                f"📺 {name.title()}\n⭐ {rating} | 📅 {year}\n🔑 Kod: {code}",
                reply_markup=menu
            )
    
    if not top_movies and not top_serials:
        await message.answer("❌ Hozircha hech narsa yo'q", reply_markup=menu)

# STATISTIKA
@dp.message(lambda message: message.text == "📊 Statistika")
async def show_stats(message: types.Message):
    if not await check_sub(message.from_user.id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
            ]
        )
        await message.answer("❗ Iltimos, botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=keyboard)
        return
    
    async with aiosqlite.connect("movies.db") as db:
# Umumiy statistika
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = await cursor.fetchone()
        
        async with db.execute("SELECT COUNT(*) FROM movies") as cursor:
            total_movies = await cursor.fetchone()
        
        async with db.execute("SELECT COUNT(*) FROM serials") as cursor:
            total_serials = await cursor.fetchone()
        
        async with db.execute("SELECT SUM(total_views) FROM users") as cursor:
            total_views = await cursor.fetchone()
        
        # Janrlar bo'yicha statistika
        genre_stats = []
        for genre in genres.keys():
            async with db.execute("SELECT COUNT(*) FROM movies WHERE genre=?", (genre,)) as cursor:
                movie_count = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*) FROM serials WHERE genre=?", (genre,)) as cursor:
                serial_count = await cursor.fetchone()
            if movie_count[0] > 0 or serial_count[0] > 0:
                genre_stats.append(f"{genres[genre]}: {movie_count[0]+serial_count[0]} ta")
        
        # Eng ko'p ko'rilgan kinolar
        async with db.execute("""
            SELECT movie_id, COUNT(*) as views 
            FROM views 
            WHERE movie_type='movie' 
            GROUP BY movie_id 
            ORDER BY views DESC 
            LIMIT 5
        """) as cursor:
            popular_movies = await cursor.fetchall()
        
        stats_text = f"📊 BOT STATISTIKASI:\n\n"
        stats_text += f"👥 Foydalanuvchilar: {total_users[0]}\n"
        stats_text += f"🎬 Kinolar: {total_movies[0]}\n"
        stats_text += f"📺 Seriallar: {total_serials[0]}\n"
        stats_text += f"👀 Jami ko'rishlar: {total_views[0] or 0}\n\n"
        stats_text += f"🎭 JANRLAR:\n" + "\n".join(genre_stats) + "\n\n"
        
        if popular_movies:
            stats_text += "🔥 ENG KO'P KO'RILGANLAR:\n"
            for i, (movie_name, views) in enumerate(popular_movies, 1):
                stats_text += f"{i}. {movie_name.title()} - {views} marta\n"
        
        await message.answer(stats_text, reply_markup=menu)

# KATEGORIYA MENU
@dp.message(lambda message: message.text == "🎭 Kategoriyalar")
async def categories_menu(message: types.Message):
    if not await check_sub(message.from_user.id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
            ]
        )
        await message.answer("❗ Iltimos, botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=keyboard)
        return
    
    await message.answer("🎭 Kategoriyalar:", reply_markup=category_menu)

# QIDIRISH
@dp.message(lambda message: message.text == "🔍 Qidirish")
async def search_prompt(message: types.Message):
    if not await check_sub(message.from_user.id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
            ]
        )
        await message.answer("❗ Iltimos, botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=keyboard)
        return
    
    await message.answer("🔍 Qidirish uchun kino yoki serial nomini yoki kodini yozing:", reply_markup=menu)

# MAIN HANDLER
@dp.message()
async def handler(message: types.Message):
    text = message.text
    
    # 🔒 OBUNA CHECK
    if not await check_sub(message.from_user.id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=CHANNEL_LINK)],
[InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
            ]
        )
        await message.answer("❗ Iltimos, botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=keyboard)
        return
    
    # 🎬 KINOLAR
    if text == "🎬 Kinolar":
        async with aiosqlite.connect("movies.db") as db:
            async with db.execute("SELECT name, code, year, rating FROM movies ORDER BY rating DESC LIMIT 50") as cursor:
                rows = await cursor.fetchall()
        
        if rows:
            result = "🎬 KINOLAR RO'YXATI:\n\n"
            for name, code, year, rating in rows:
                result += f"📽 {name.title()} ({code})\n   ⭐ {rating} | 📅 {year}\n\n"
            await message.answer(result[:4000], reply_markup=menu)
        else:
            await message.answer("❌ Hozircha kino yo'q", reply_markup=menu)
    
    # 📺 SERIAL
    elif text == "📺 Seriallar":
        async with aiosqlite.connect("movies.db") as db:
            async with db.execute("SELECT DISTINCT name, code, year, rating FROM serials ORDER BY rating DESC LIMIT 50") as cursor:
                rows = await cursor.fetchall()
        
        if rows:
            result = "📺 SERIALLAR RO'YXATI:\n\n"
            for name, code, year, rating in rows:
                result += f"📺 {name.title()} ({code})\n   ⭐ {rating} | 📅 {year}\n\n"
            await message.answer(result[:4000], reply_markup=menu)
        else:
            await message.answer("❌ Hozircha serial yo'q", reply_markup=menu)
    
    # QIDIRISH
    else:
        async with aiosqlite.connect("movies.db") as db:
            # Kino qidirish
            async with db.execute(
                "SELECT name, file_id, rating, year, duration FROM movies WHERE name LIKE ? OR code LIKE ? ORDER BY rating DESC",
                (f"%{text.lower()}%", f"%{text.lower()}%")
            ) as cursor:
                movies = await cursor.fetchall()
            
            # Serial qidirish
            async with db.execute(
                "SELECT name, part, file_id, rating, year FROM serials WHERE name LIKE ? OR code LIKE ? ORDER BY part",
                (f"%{text.lower()}%", f"%{text.lower()}%")
            ) as cursor:
                serials = await cursor.fetchall()
        
        if movies:
            for name, file_id, rating, year, duration in movies:
                await message.answer_video(
                    video=file_id,
                    caption=f"🎬 {name.title()}\n⭐ {rating} | 📅 {year} | ⏱ {duration} min",
                    reply_markup=menu
                )
                await add_view(message.from_user.id, name, "movie")
        
        elif serials:
            serial_dict = {}
            for name, part, file_id, rating, year in serials:
                if name not in serial_dict:
                    serial_dict[name] = []
                serial_dict[name].append((part, file_id, rating, year))
            
            for name, parts in serial_dict.items():
                rating = parts[0][2]
                year = parts[0][3]
                await message.answer(f"📺 {name.title()} | ⭐ {rating} | 📅 {year}\n{len(parts)} qism:", reply_markup=menu)
                for part, file_id, _, _ in parts:
                    await message.answer_video(
                        video=file_id,
                        caption=f"📺 {name.title()} {part}-qism",
                        reply_markup=menu
                    )
                    await add_view(message.from_user.id, f"{name} {part}-qism", "serial")
        
        else:
            await message.answer("❌ Hech narsa topilmadi\n\n💡 Maslahat: Qidirish uchun:\n• Kino/serial nomi\n• Kod (masalan: tit123)\n• Kategoriya bo'yicha izlash", reply_markup=menu)

# MAIN
async def main():
    await init_db()
    print("Bot ishga tushdi...")
    print(f"Janrlar: {', '.join(genres.keys())}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())