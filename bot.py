import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Берём токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("❌ Ошибка: не найден BOT_TOKEN в переменных окружения.")
    raise SystemExit(1)


# ====== ЛОГИКА АНКЕТЫ ======

QUESTIONS = {
    1: {
        "text": (
            "📋 Анкета кредитной истории\n\n"
            "❓ Вопрос 1/3:\n"
            "<b>Какая у вас кредитная история?</b>"
        ),
        "buttons": [
            [InlineKeyboardButton("Хорошая ✅", callback_data="q1_good")],
            [InlineKeyboardButton("Средняя ⚠️", callback_data="q1_medium")],
            [InlineKeyboardButton("Плохая ❌", callback_data="q1_bad")],
        ],
    },
    2: {
        "text": (
            "❓ Вопрос 2/3:\n"
            "<b>Есть ли у вас текущие просрочки по кредитам?</b>"
        ),
        "buttons": [
            [InlineKeyboardButton("Нет ✅", callback_data="q2_no")],
            [InlineKeyboardButton("Редко", callback_data="q2_some")],
            [InlineKeyboardButton("Часто ❌", callback_data="q2_many")],
        ],
    },
    3: {
        "text": (
            "❓ Вопрос 3/3:\n"
            "<b>Какой у вас ежемесячный доход?</b>"
        ),
        "buttons": [
            [InlineKeyboardButton("> 100 000 ₽", callback_data="q3_high")],
            [InlineKeyboardButton("50–100 000 ₽", callback_data="q3_mid")],
            [InlineKeyboardButton("< 50 000 ₽", callback_data="q3_low")],
        ],
    },
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — всегда начинает опрос сначала."""
    context.user_data.clear()
    context.user_data["step"] = 1

    q = QUESTIONS[1]
    keyboard = InlineKeyboardMarkup(q["buttons"])

    await update.message.reply_text(
        q["text"],
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Единственный обработчик всех кнопок."""
    query = update.callback_query
    await query.answer()

    data = query.data

    # Перезапуск с кнопки
    if data == "restart":
        context.user_data.clear()
        context.user_data["step"] = 1
        q = QUESTIONS[1]
        keyboard = InlineKeyboardMarkup(q["buttons"])
        await query.edit_message_text(
            q["text"],
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return

    # Текущий шаг (по умолчанию 1)
    step = context.user_data.get("step", 1)

    # Сохраняем ответ по шагу (answer_1, answer_2, answer_3)
    context.user_data[f"answer_{step}"] = data

    # Если ещё есть вопросы — идём к следующему
    if step < 3:
        step += 1
        context.user_data["step"] = step
        q = QUESTIONS[step]
        keyboard = InlineKeyboardMarkup(q["buttons"])

        await query.edit_message_text(
            q["text"],
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return

    # Если это был последний вопрос — считаем результат
    await show_result(query, context)


async def show_result(query, context: ContextTypes.DEFAULT_TYPE):
    a1 = context.user_data.get("answer_1")
    a2 = context.user_data.get("answer_2")
    a3 = context.user_data.get("answer_3")

    score = 0

    # История
    if a1 == "q1_good":
        score += 40
    elif a1 == "q1_medium":
        score += 20
    else:
        score += 5

    # Просрочки
    if a2 == "q2_no":
        score += 30
    elif a2 == "q2_some":
        score += 10
    else:
        score += 0

    # Доход
    if a3 == "q3_high":
        score += 30
    elif a3 == "q3_mid":
        score += 15
    else:
        score += 5

    if score >= 80:
        text = (
            "🎉 <b>Отличная кредитная анкета!</b>\n\n"
            f"Ваш условный рейтинг: <b>{score}/100</b>\n\n"
            "Шансы на одобрение высокого кредита — очень высокие."
        )
    elif score >= 50:
        text = (
            "✅ <b>Неплохо!</b>\n\n"
            f"Ваш условный рейтинг: <b>{score}/100</b>\n\n"
            "Шансы на одобрение есть, но условия могут быть средними."
        )
    else:
        text = (
            "⚠️ <b>Слабая анкета.</b>\n\n"
            f"Ваш условный рейтинг: <b>{score}/100</b>\n\n"
            "Нужно улучшать историю и снижать просрочки."
        )

    # Кнопки: сначала "Оформить" (ссылка), ниже — "Пройти ещё раз"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ОФОРМИТЬ", url="https://t.me/ekapusta_robot/ekapusta")],
        [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data="restart")],
    ])

    await query.edit_message_text(
        text + "\n\n<b>ОФОРМИТЬ</b> — перейдите по ссылке ниже.\n\nКоманда /start тоже перезапускает анкету.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))

    app.run_polling()


if __name__ == "__main__":
    main()
