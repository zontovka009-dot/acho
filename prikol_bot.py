import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "ВАШ_ТОКЕН"

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

async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🚀 Запустить процесс", callback_data="confirm_0")]]
    await update.message.reply_text("Нажми кнопку чтобы запустить процесс:", reply_markup=InlineKeyboardMarkup(kb))

async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user.first_name

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
            await asyncio.sleep(1)
            msg = await query.message.reply_text(f"🔄 Процесс ебли мамы {user} запущен\n\n▓░░░░░░░░░ 0%")
            for i in range(1, 11):
                await asyncio.sleep(5)
                filled = "▓" * i + "░" * (10 - i)
                await msg.edit_text(f"🔄 Процесс ебли мамы {user} запущен\n\n{filled} {i*10}%")
            await msg.edit_text(f"✅ Процесс ебли мамы {user} завершён успешно 💀")

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
