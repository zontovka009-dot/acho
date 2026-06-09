import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "ВАШ_ТОКЕН_СЮДА"

CONFIRMS = [
    "Ты уверен?",
    "Точно уверен?",
    "Ну реально точно?",
    "Последний шанс отказаться...",
    "Ладно, но ты сам попросил. Уверен?",
    "ФИНАЛЬНОЕ предупреждение. Уверен???",
]

CANCELS = [
    "Окей стоп, ты уверен что хочешь отменить?",
    "Серьёзно отменяешь?",
    "Ну и зря. Точно отменяешь?",
    "Последний шанс передумать...",
    "Ладно ладно, отменяем. Уверен в отмене?",
]

def generate_puzzle():
    ptype = random.choice(["math", "sequence", "riddle"])

    if ptype == "math":
        a = random.randint(2, 15)
        b = random.randint(2, 15)
        op = random.choice(["+", "-", "*"])
        if op == "+":
            answer = a + b
        elif op == "-":
            answer = a - b
        else:
            answer = a * b
        question = f"🧮 Реши пример: {a} {op} {b} = ?"
        wrong = [answer + random.randint(1, 5), answer - random.randint(1, 5), answer + random.randint(6, 10)]
        wrong = [w for w in wrong if w != answer][:3]
        options = wrong + [answer]
        random.shuffle(options)
        return question, str(answer), [str(o) for o in options]

    elif ptype == "sequence":
        start = random.randint(1, 10)
        step = random.randint(2, 7)
        seq = [start + step * i for i in range(4)]
        answer = start + step * 4
        question = f"🔢 Продолжи последовательность: {seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}, ?"
        wrong = [answer + step, answer - step, answer + random.randint(1, 4)]
        wrong = [w for w in wrong if w != answer][:3]
        options = wrong + [answer]
        random.shuffle(options)
        return question, str(answer), [str(o) for o in options]

    else:
        riddles = [
            ("У меня есть города, но нет домов. Есть горы, но нет деревьев. Есть вода, но нет рыбы. Что я?", "Карта",
             ["Глобус", "Атлас", "Фото", "Карта"]),
            ("Чем больше берёшь — тем больше становится. Что это?", "Яма",
             ["Яма", "Долг", "Дыра", "Мешок"]),
            ("Есть у каждого, но нельзя отдать другому. Что это?", "Имя",
             ["Имя", "Тень", "Голос", "Душа"]),
            ("Чего в реке не утопишь, в огне не сожжёшь?", "Лёд",
             ["Лёд", "Камень", "Вода", "Время"]),
        ]
        q, answer, options = random.choice(riddles)
        shuffled = options[:]
        random.shuffle(shuffled)
        return f"🤔 Загадка: {q}", answer, shuffled


async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🚀 Запустить процесс", callback_data="confirm_0")]]
    await update.message.reply_text("Нажми кнопку чтобы запустить процесс:", reply_markup=InlineKeyboardMarkup(kb))


async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user.first_name

    # --- Подтверждения запуска ---
    if data.startswith("confirm_"):
        step = int(data.split("_")[1])
        if step < len(CONFIRMS):
            kb = [
                [InlineKeyboardButton("✅ Да", callback_data=f"confirm_{step+1}")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_0")],
            ]
            await query.edit_message_text(CONFIRMS[step], reply_markup=InlineKeyboardMarkup(kb))
        else:
            # Все подтверждения пройдены — показываем головоломку
            question, answer, options = generate_puzzle()
            ctx.user_data["puzzle_answer"] = answer
            kb = [[InlineKeyboardButton(opt, callback_data=f"puzzle_{opt}")] for opt in options]
            await query.edit_message_text(
                f"⚠️ СТОП! Чтобы запустить процесс, сначала реши задачу:\n\n{question}",
                reply_markup=InlineKeyboardMarkup(kb)
            )

    # --- Ответ на головоломку ---
    elif data.startswith("puzzle_"):
        chosen = data[len("puzzle_"):]
        correct = ctx.user_data.get("puzzle_answer", "")

        if chosen == correct:
            # Правильный ответ — начинаем процесс, но сначала 3 попытки отмены
            ctx.user_data["cancel_wins"] = 0
            kb = [
                [InlineKeyboardButton("✅ Да", callback_data="win_cancel_yes")],
                [InlineKeyboardButton("❌ Нет", callback_data="win_cancel_no")],
            ]
            await query.edit_message_text("✅ Правильно! Процесс запускается...\n\nПодожди, отменить?", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await query.edit_message_text(
                f"❌ Неверно! Правильный ответ: {correct}\n\n💀 Процесс ебли мамы {user} запущен без предупреждения..."
            )

    # --- Победные отмены (после правильного ответа) ---
    elif data == "win_cancel_yes":
        kb = [
            [InlineKeyboardButton("Нет", callback_data="win_cancel_no2")],
            [InlineKeyboardButton("Нет (другая кнопка)", callback_data="win_cancel_no2")],
        ]
        await query.edit_message_text("🤔 Точно отменить?", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "win_cancel_no":
        wins = ctx.user_data.get("cancel_wins", 0) + 1
        ctx.user_data["cancel_wins"] = wins
        if wins < 3:
            kb = [
                [InlineKeyboardButton("✅ Да", callback_data="win_cancel_yes")],
                [InlineKeyboardButton("❌ Нет", callback_data="win_cancel_no")],
            ]
            await query.edit_message_text(f"😤 Ладно... Но может всё-таки отменить? (попытка {wins}/3)", reply_markup=InlineKeyboardMarkup(kb))
        else:
            # Все 3 попытки пройдены — запускаем настоящий процесс
            await query.edit_message_text("⚙️ Ладно, запускаем...")
            await asyncio.sleep(1)
            msg = await query.message.reply_text(f"🔄 Процесс ебли мамы {user} запущен\n\n▓░░░░░░░░░ 0%")
            for i in range(1, 11):
                await asyncio.sleep(5)
                filled = "▓" * i + "░" * (10 - i)
                await msg.edit_text(f"🔄 Процесс ебли мамы {user} запущен\n\n{filled} {i*10}%")
            await msg.edit_text(f"🎉 Поздравляю, {user}! Ты прошёл все испытания.\nМама в безопасности 💪")

    elif data == "win_cancel_no2":
        # Нажал "нет" на "точно отменить" — через 3 сек выдаём "Ладно, живи"
        await query.edit_message_text("😏 Правильный выбор. Думаю над этим...")
        await asyncio.sleep(3)
        kb = [[InlineKeyboardButton("Ладно, живи 🕊️", callback_data="win_survive")]]
        await query.message.reply_text("Ладно, живи.", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "win_survive":
        await query.edit_message_text("🎉 Процесс отменён. Ты выжил. На этот раз.")

    # --- Обычная отмена до головоломки ---
    elif data.startswith("cancel_"):
        step = int(data.split("_")[1])
        if step < len(CANCELS):
            kb = [
                [InlineKeyboardButton("✅ Да, отменить", callback_data=f"cancel_{step+1}")],
                [InlineKeyboardButton("🔙 Нет, продолжить", callback_data=f"confirm_{len(CONFIRMS)//2}")],
            ]
            await query.edit_message_text(CANCELS[step], reply_markup=InlineKeyboardMarkup(kb))
        else:
            await query.edit_message_text("😮‍💨 Процесс отменён. Трус.")


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()


if __name__ == "__main__":
    main()
