import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8843772612:AAFndhGEVQDVApPamGJizAmuDNpGM8ijhUY"

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
        answer = a + b if op == "+" else (a - b if op == "-" else a * b)
        question = f"🧮 Реши пример: {a} {op} {b} = ?"
        wrong = list({answer + random.randint(1,5), answer - random.randint(1,4), answer + random.randint(6,10)} - {answer})[:3]
        options = (wrong + [answer])[:4]
        random.shuffle(options)
        return question, str(answer), [str(o) for o in options]

    elif ptype == "sequence":
        start = random.randint(1, 10)
        step = random.randint(2, 7)
        seq = [start + step * i for i in range(4)]
        answer = start + step * 4
        question = f"🔢 Последовательность: {seq[0]}, {seq[1]}, {seq[2]}, {seq[3]}, ?"
        wrong = list({answer + step, answer - step, answer + random.randint(1,4)} - {answer})[:3]
        options = (wrong + [answer])[:4]
        random.shuffle(options)
        return question, str(answer), [str(o) for o in options]

    else:
        riddles = [
            ("У меня есть города, но нет домов. Есть горы, но нет деревьев. Что я?", "Карта",
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


async def run_process(message, user, ctx, chat_id):
    """Запускает прогресс-бар, на рандомном проценте останавливает и даёт загадку."""
    stop_at = random.choice([30, 40, 50, 60, 70])  # рандомный процент для загадки
    question, answer, options = generate_puzzle()
    ctx.user_data["puzzle_answer"] = answer
    ctx.user_data["user_name"] = user

    msg = await message.reply_text(f"🔄 Процесс ебли мамы {user} запущен\n\n░░░░░░░░░░ 0%")
    ctx.user_data["progress_msg_id"] = msg.message_id
    ctx.user_data["progress_chat_id"] = chat_id

    for i in range(1, 11):
        await asyncio.sleep(5)
        pct = i * 10
        filled = "▓" * i + "░" * (10 - i)

        if pct == stop_at:
            # Стоп — показываем загадку
            kb = [[InlineKeyboardButton(opt, callback_data=f"puzzle_{opt}")] for opt in options]
            await msg.edit_text(
                f"🔄 Процесс ебли мамы {user} запущен\n\n{filled} {pct}%\n\n"
                f"⚠️ СТОП! Процесс заморожен. Реши загадку чтобы остановить его:\n\n{question}",
                reply_markup=InlineKeyboardMarkup(kb)
            )
            ctx.user_data["frozen_msg"] = msg
            ctx.user_data["frozen_pct"] = pct
            ctx.user_data["frozen_filled"] = filled
            return  # выходим, дальше обрабатывает button()

        await msg.edit_text(f"🔄 Процесс ебли мамы {user} запущен\n\n{filled} {pct}%")

    # Если загадка не встретилась (не должно случиться, но на всякий)
    await msg.edit_text(f"💀 Процесс ебли мамы {user} завершён. Никто не успел остановить.")


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
            await query.edit_message_text("⚙️ Запускаем...")
            asyncio.create_task(run_process(query.message, user, ctx, query.message.chat_id))

    # --- Ответ на загадку во время процесса ---
    elif data.startswith("puzzle_"):
        chosen = data[len("puzzle_"):]
        correct = ctx.user_data.get("puzzle_answer", "")
        user_name = ctx.user_data.get("user_name", user)
        msg = ctx.user_data.get("frozen_msg")
        filled = ctx.user_data.get("frozen_filled", "▓▓▓▓▓░░░░░")
        pct = ctx.user_data.get("frozen_pct", 50)

        if chosen == correct:
            # Правильно — предлагаем отменить процесс (3 раза)
            ctx.user_data["cancel_wins"] = 0
            kb = [
                [InlineKeyboardButton("✅ Да", callback_data="win_cancel_yes")],
                [InlineKeyboardButton("❌ Нет", callback_data="win_cancel_no")],
            ]
            if msg:
                await msg.edit_text(
                    f"🔄 Процесс ебли мамы {user_name} запущен\n\n{filled} {pct}%\n\n✅ Правильно! Отменить процесс?",
                    reply_markup=InlineKeyboardMarkup(kb)
                )
        else:
            if msg:
                await msg.edit_text(
                    f"🔄 Процесс ебли мамы {user_name} запущен\n\n{filled} {pct}%\n\n"
                    f"❌ Неверно! Правильный ответ: {correct}\n\n💀 Процесс продолжается без остановки..."
                )
            # Продолжаем прогресс с места где остановились
            asyncio.create_task(continue_process(msg, user_name, pct))

    # --- Победные отмены (после правильного ответа на загадку) ---
    elif data == "win_cancel_yes":
        msg = ctx.user_data.get("frozen_msg")
        user_name = ctx.user_data.get("user_name", user)
        filled = ctx.user_data.get("frozen_filled", "")
        pct = ctx.user_data.get("frozen_pct", 50)
        kb = [
            [InlineKeyboardButton("Нет", callback_data="win_cancel_no2")],
            [InlineKeyboardButton("Нет (другая кнопка)", callback_data="win_cancel_no2")],
        ]
        if msg:
            await msg.edit_text(
                f"🔄 Процесс ебли мамы {user_name} запущен\n\n{filled} {pct}%\n\n🤔 Точно отменить?",
                reply_markup=InlineKeyboardMarkup(kb)
            )

    elif data == "win_cancel_no":
        wins = ctx.user_data.get("cancel_wins", 0) + 1
        ctx.user_data["cancel_wins"] = wins
        msg = ctx.user_data.get("frozen_msg")
        user_name = ctx.user_data.get("user_name", user)
        filled = ctx.user_data.get("frozen_filled", "")
        pct = ctx.user_data.get("frozen_pct", 50)
        if wins < 3:
            kb = [
                [InlineKeyboardButton("✅ Да", callback_data="win_cancel_yes")],
                [InlineKeyboardButton("❌ Нет", callback_data="win_cancel_no")],
            ]
            if msg:
                await msg.edit_text(
                    f"🔄 Процесс ебли мамы {user_name} запущен\n\n{filled} {pct}%\n\n😤 Ладно... Но может всё-таки отменить? ({wins}/3)",
                    reply_markup=InlineKeyboardMarkup(kb)
                )
        else:
            # Все 3 попытки пройдены — процесс продолжается и завершается
            if msg:
                await msg.edit_text(f"😏 Ну и ладно. Процесс продолжается...\n\n{filled} {pct}%")
            asyncio.create_task(continue_process(msg, user_name, pct))

    elif data == "win_cancel_no2":
        msg = ctx.user_data.get("frozen_msg")
        user_name = ctx.user_data.get("user_name", user)
        filled = ctx.user_data.get("frozen_filled", "")
        pct = ctx.user_data.get("frozen_pct", 50)
        if msg:
            await msg.edit_text(
                f"✅ Процесс ебли мамы {user_name} остановлен на {pct}%\n\n"
                f"Думаю над этим..."
            )
        await asyncio.sleep(3)
        kb = [[InlineKeyboardButton("Ладно, живи 🕊️", callback_data="win_survive")]]
        await query.message.reply_text("Ладно, живи.", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "win_survive":
        user_name = ctx.user_data.get("user_name", user)
        await query.edit_message_text(f"🎉 Поздравляю, {user_name}! Ты выжил. На этот раз. 💪")

    # --- Обычная отмена до запуска ---
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


async def continue_process(msg, user, start_pct):
    """Продолжает прогресс-бар с места остановки до 100%."""
    start_i = start_pct // 10
    for i in range(start_i + 1, 11):
        await asyncio.sleep(5)
        pct = i * 10
        filled = "▓" * i + "░" * (10 - i)
        if msg:
            try:
                await msg.edit_text(f"🔄 Процесс ебли мамы {user} запущен\n\n{filled} {pct}%")
            except Exception:
                pass
    if msg:
        try:
            await msg.edit_text(f"💀 Процесс ебли мамы {user} завершён успешно.")
        except Exception:
            pass


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()


if __name__ == "__main__":
    main()
