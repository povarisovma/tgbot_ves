import os
import re
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
from chart import build_chart, build_pressure_chart

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("⚖️ График веса"), KeyboardButton("⚖️ График веса (3 мес.)")],
        [KeyboardButton("⚖️ История взвешиваний"), KeyboardButton("🗑 Удалить взвешивание")],
        [KeyboardButton("🫀 График давления"), KeyboardButton("🫀 График давления (7 дн.)")],
        [KeyboardButton("🫀 История измерений"), KeyboardButton("🗑 Удалить измерение")],
    ],
    resize_keyboard=True,
)

_PRESSURE_RE = re.compile(r'^(\d+)[-/ ](\d+)(?:[-/ ](\d+))?$')


def parse_pressure(text: str):
    m = _PRESSURE_RE.match(text.strip())
    if not m:
        return None
    systolic = int(m.group(1))
    diastolic = int(m.group(2))
    pulse = int(m.group(3)) if m.group(3) else None
    if not (60 <= systolic <= 250 and 40 <= diastolic <= 150):
        return None
    if pulse is not None and not (30 <= pulse <= 220):
        return None
    return systolic, diastolic, pulse


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добрый день, друг! 👋\n\n"
        "Этот бот помогает следить за здоровьем — записывает вес и давление, строит графики динамики.\n\n"
        "⚖️ *Вес* — отправь число, например: *75.3*\n"
        "Одна запись в день.\n\n"
        "🫀 *Давление* — отправь два или три числа через /, - или пробел:\n"
        "*120/80* или *120/80/70* (с пульсом)\n"
        "Одна запись утром (05:00–14:59) и одна вечером (15:00–04:59).\n\n"
        "Остальное — через кнопки внизу 👇",
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
        f"👥 Пользователей: *{s['total_users']}*\n\n"
        f"⚖️ *Взвешивания:*\n"
        f"   Всего записей: *{s['total_weight']}*\n"
        f"   Записей сегодня: *{s['today_weight']}*\n"
        f"   Удалений всего: *{s['total_weight_del']}*\n"
        f"   Удалений сегодня: *{s['today_weight_del']}*\n\n"
        f"🫀 *Давление:*\n"
        f"   Всего записей: *{s['total_pressure']}*\n"
        f"   Сегодня утром: *{s['today_pressure_morning']}*\n"
        f"   Сегодня вечером: *{s['today_pressure_evening']}*\n"
        f"   Удалений всего: *{s['total_pressure_del']}*\n"
        f"   Удалений сегодня: *{s['today_pressure_del']}*",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text == "⚖️ График веса":
        await send_chart(update, user_id)
        return

    if text == "⚖️ График веса (3 мес.)":
        await send_chart(update, user_id, months=3)
        return

    if text == "⚖️ История взвешиваний":
        await send_history(update, user_id)
        return

    if text == "🗑 Удалить взвешивание":
        await delete_last(update, user_id)
        return

    if text == "🫀 График давления":
        await send_pressure_chart(update, user_id)
        return

    if text == "🫀 График давления (7 дн.)":
        await send_pressure_chart(update, user_id, days=7)
        return

    if text == "🫀 История измерений":
        await send_pressure_history(update, user_id)
        return

    if text == "🗑 Удалить измерение":
        await delete_last_pressure(update, user_id)
        return

    # пробуем распознать давление (два или три числа через /, - или пробел)
    pressure = parse_pressure(text)
    if pressure is not None:
        systolic, diastolic, pulse = pressure
        period = db.get_period()
        if db.already_recorded_pressure(user_id, period):
            period_label = "утреннее" if period == "morning" else "вечернее"
            other_label = "вечернее" if period == "morning" else "утреннее"
            await update.message.reply_text(
                f"⚠️ {period_label.capitalize()} давление за сегодня уже записано.\n"
                f"{other_label.capitalize()} можно записать {'после 15:00' if period == 'morning' else 'с 05:00 завтра'}.",
                reply_markup=MAIN_KEYBOARD,
            )
            return
        period = db.add_pressure(user_id, systolic, diastolic, pulse)
        period_label = "утро" if period == "morning" else "вечер"
        pulse_part = f", пульс *{pulse}*" if pulse else ""
        await update.message.reply_text(
            f"✅ Записал давление ({period_label}): *{systolic}/{diastolic}*{pulse_part}",
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    # пробуем распознать вес
    try:
        weight = float(text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(
            "Не понимаю 🤔\n"
            "• Вес: *75.3*\n"
            "• Давление: *120/80* или *120/80/70* (с пульсом)",
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
        f"✅ Записал вес: *{weight:.1f} кг*",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


async def delete_last(update: Update, user_id: int):
    if db.deletions_today(user_id) >= 3:
        await update.message.reply_text(
            "⛔️ Сегодня ты уже удалял записи 3 раза. Лимит исчерпан до завтра.",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    weight = db.delete_last_weight(user_id)
    if weight is None:
        await update.message.reply_text(
            "Записей нет — нечего удалять.",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    remaining = 3 - db.deletions_today(user_id)
    await update.message.reply_text(
        f"🗑 Последняя запись удалена: *{weight:.1f} кг*\n"
        f"Осталось удалений сегодня: *{remaining}*",
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


async def send_chart(update: Update, user_id: int, months: int = None):
    if months:
        rows = db.get_history_months(user_id, months)
        caption = f"📊 Динамика веса за последние {months} месяца(-ев)"
    else:
        rows = db.get_history(user_id)
        caption = "📊 Динамика веса за всё время"

    if not rows:
        await update.message.reply_text("Записей за этот период нет.")
        return

    if len(rows) < 2:
        await update.message.reply_text(
            "Нужно хотя бы 2 записи, чтобы построить график. Пока есть только одна."
        )
        return

    await update.message.reply_text("Строю график… ⏳")
    buf = build_chart(rows)
    await update.message.reply_photo(photo=buf, caption=caption)


async def send_pressure_history(update: Update, user_id: int):
    rows = db.get_pressure_history(user_id)
    if not rows:
        await update.message.reply_text("Записей давления пока нет.")
        return

    period_labels = {"morning": "утро", "evening": "вечер"}
    lines = []
    for r in rows:
        date = r["date"][:10]
        time = r["date"][11:16]
        period = period_labels.get(r["period"], r["period"])
        pulse_part = f", пульс {r['pulse']}" if r["pulse"] else ""
        lines.append(f"{date} {time} ({period})  —  {r['systolic']}/{r['diastolic']}{pulse_part}")

    text = "📋 *История давления:*\n\n" + "\n".join(lines)
    if len(text) > 4096:
        text = text[-4093:] + "..."

    await update.message.reply_text(text, parse_mode="Markdown")


async def send_pressure_chart(update: Update, user_id: int, days: int = None):
    if days:
        rows = db.get_pressure_history_days(user_id, days)
        caption = f"🫀 Динамика давления за последние {days} дней"
    else:
        rows = db.get_pressure_history(user_id)
        caption = "🫀 Динамика давления за всё время"

    if not rows:
        await update.message.reply_text("Записей давления за этот период нет.")
        return
    if len(rows) < 2:
        await update.message.reply_text(
            "Нужно хотя бы 2 записи, чтобы построить график."
        )
        return

    await update.message.reply_text("Строю график давления… ⏳")
    buf = build_pressure_chart(rows)
    await update.message.reply_photo(photo=buf, caption=caption)


async def delete_last_pressure(update: Update, user_id: int):
    if db.pressure_deletions_today(user_id) >= 6:
        await update.message.reply_text(
            "⛔️ Сегодня ты уже удалял измерения давления 6 раз. Лимит исчерпан до завтра.",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    row = db.delete_last_pressure(user_id)
    if row is None:
        await update.message.reply_text(
            "Записей давления нет — нечего удалять.",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    remaining = 6 - db.pressure_deletions_today(user_id)
    pulse_part = f", пульс {row['pulse']}" if row["pulse"] else ""
    await update.message.reply_text(
        f"🗑 Последнее измерение давления удалено: *{row['systolic']}/{row['diastolic']}*{pulse_part}\n"
        f"Осталось удалений сегодня: *{remaining}*",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


def main():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
