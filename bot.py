import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import db
from chart import build_chart

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("📊 График"), KeyboardButton("📋 История")]],
    resize_keyboard=True,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добрый день, друг! 👋\n\n"
        "Данный бот предназначен для ведения учёта массы тела и поможет всем желающим следить за своим весом.\n\n"
        "Просто отправь число — например: *75.3*\n"
        "Я запишу его, и ты всегда сможешь посмотреть историю или график своих взвешиваний.",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У тебя нет доступа к этой команде.")
        return

    s = db.get_stats()
    await update.message.reply_text(
        f"📊 *Статистика бота*\n\n"
        f"👥 Пользователей: *{s['total_users']}*\n"
        f"📝 Всего записей: *{s['total_records']}*\n"
        f"📅 Записей сегодня: *{s['today_records']}*",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text == "📊 График":
        await send_chart(update, user_id)
        return

    if text == "📋 История":
        await send_history(update, user_id)
        return

    # пробуем распознать число
    try:
        weight = float(text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(
            "Не понимаю 🤔 Отправь число, например: *75.3*",
            parse_mode="Markdown",
        )
        return

    if weight <= 0 or weight > 500:
        await update.message.reply_text("Вес должен быть от 1 до 500 кг.")
        return

    if db.already_recorded_today(user_id):
        await update.message.reply_text(
            "⚠️ Ты уже записывал вес сегодня. Следующая запись доступна завтра.",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    db.add_weight(user_id, weight)
    await update.message.reply_text(
        f"✅ Записал: *{weight:.1f} кг*",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


async def send_history(update: Update, user_id: int):
    rows = db.get_history(user_id)
    if not rows:
        await update.message.reply_text("Записей пока нет. Отправь своё первое взвешивание!")
        return

    lines = [f"{r['date']}  —  {r['weight']:.1f} кг" for r in rows]
    text = "📋 *История взвешиваний:*\n\n" + "\n".join(lines)

    # Telegram ограничивает сообщение 4096 символами
    if len(text) > 4096:
        text = text[-4093:] + "..."

    await update.message.reply_text(text, parse_mode="Markdown")


async def send_chart(update: Update, user_id: int):
    rows = db.get_history(user_id)
    if not rows:
        await update.message.reply_text("Записей пока нет. Отправь своё первое взвешивание!")
        return

    if len(rows) < 2:
        await update.message.reply_text(
            "Нужно хотя бы 2 записи, чтобы построить график. Пока есть только одна."
        )
        return

    await update.message.reply_text("Строю график… ⏳")
    buf = build_chart(rows)
    await update.message.reply_photo(photo=buf, caption="📊 Динамика твоего веса")


def main():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
