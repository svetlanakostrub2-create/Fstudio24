import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ReplyKeyboardMarkup,
)

# === ЗАМЕНИ НА СВОИ ДАННЫЕ ===
BOT_TOKEN = "7978471971:AAGgAFKwEoBCPtxStPCK1aF06Iz7vuoUWQo"  # ← ВСТАВЬ ТОКЕН В КАВЫЧКАХ
YOUR_TELEGRAM_ID = 1606381134  # ← ВСТАВЬ СВОЙ ID (ЦИФРЫ, БЕЗ КАВЫЧЕК)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name)

user_sessions = {}

MAIN_MENU = [
    ["печать фото", "печать документов"],
    ["реставрация фото", "изготовление визиток/буклетов/наклеек"],
    ["оцифровка аудио и видео кассет и фотопленок"],
    ["термопечать на футболках/кружках и тд"],
    ["фотошоп", "другое"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = {"step": "main_menu", "data": {}}
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Добрый день! Какая услуга вас интересует?", reply_markup=reply_markup)

async def send_application(user_id, data, context):
    lines = ["📥 НОВАЯ ЗАЯВКА"]
    for k, v in data.items():
        if k == "услуга": lines.append(f"🔹 {v}")
        elif k == "формат": lines.append(f"📏 {v}")
        elif k == "бумага": lines.append(f"📄 {v}")
        elif k == "примечание": lines.append(f"📝 {v}")
        elif k == "файлы": lines.append(f"📎 {len(v)} файлов")
    msg = "\n".join(lines)
    try:
        await context.bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=msg)
    except Exception as e:
        logger.error(f"Ошибка: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id    text = update.message.text.strip() if update.message.text else ""
    
    if user_id not in user_sessions:
        return await start(update, context)

    session = user_sessions[user_id]
    step = session["step"]
    data = session["data"]

    if step == "confirmation":
        if any(word in text.lower() for word in ["да", "верно", "отправить"]):
            await send_application(user_id, data, context)
            await update.message.reply_text("✅ Заявка отправлена!")
            user_sessions.pop(user_id, None)
        elif any(word in text.lower() for word in ["нет", "заново"]):
            await start(update, context)
        else:
            await update.message.reply_text("Выберите: ✅ Да, отправить или ↩️ Нет, начать заново.")
        return

    if step == "main_menu":
        if text.lower() not in [btn.lower() for row in MAIN_MENU for btn in row]:
            return await update.message.reply_text("Выберите услугу из списка.")
        data["услуга"] = text
        if "печать фото" in text.lower():
            kb = [["10×15 (А6)", "15×20 (А5)"], ["21×30 (А4)", "30×42 (А3)"]]
            await update.message.reply_text("Формат?", reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True))
            session["step"] = "photo_format"
        elif "печать документов" in text.lower():
            await update.message.reply_text("Пришлите файлы и укажите: цветная/ч/б, кол-во копий")
            session["step"] = "docs_info"
        else:
            await update.message.reply_text("Опишите детали или пришлите файлы.")
            session["step"] = "other_info"

    elif step == "photo_format":
        if text not in ["10×15 (А6)", "15×20 (А5)", "21×30 (А4)", "30×42 (А3)"]:
            return await update.message.reply_text("Выберите формат.")
        data["формат"] = text
        kb = [["глянцевая", "матовая"]]
        await update.message.reply_text("Бумага?", reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True))
        session["step"] = "photo_paper"

    elif step == "photo_paper":
if text.lower() not in ["глянцевая", "матовая"]:
            return await update.message.reply_text("Выберите: глянцевая или матовая.")
        data["бумага"] = text.lower()
        await update.message.reply_text("Пришлите фотографии.")
        session["step"] = "photo_files"
    elif step in ["photo_files", "docs_info", "other_info"]:
        if text:
            data["примечание"] = text
        summary = (
            f"Проверьте заказ:\n"
            f"🔹 Услуга: {data.get('услуга', '-')}\n"
            f"📏 Формат: {data.get('формат', '-')}\n"
            f"📄 Бумага: {data.get('бумага', '-')}\n"
            f"📎 Файлов: {len(data.get('файлы', []))}\n"
            f"---------------------\n"
            f"Всё верно?"
        )
        kb = [["✅ Да, отправить", "↩️ Нет, начать заново"]]
        await update.message.reply_text(summary, reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True))
        session["step"] = "confirmation"

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        return
    session = user_sessions[user_id]
    if "файлы" not in session["data"]:
        session["data"]["файлы"] = []
    if update.message.photo:
        session["data"]["файлы"].append("photo")
    elif update.message.document:
        session["data"]["файлы"].append("document")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file))

if name == "main":
    app.run_polling()
