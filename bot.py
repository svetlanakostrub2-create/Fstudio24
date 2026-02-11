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
# === НАСТРОЙКИ ===
BOT_TOKEN = "7978471971:AAGgAFKwEoBCPtxStPCK1aF06Iz7vuoUWQo"  # 
YOUR_TELEGRAM_ID = 1606381134  #

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name)

# Хранилище данных пользователей
user_sessions = {}

# Главное меню
MAIN_MENU = [
    ["печать фото", "печать документов"],
    ["реставрация фото", "изготовление визиток/буклетов/наклеек"],
    ["оцифровка аудио и видео кассет и фотопленок"],
    ["термопечать на футболках/кружках и тд"],
    ["фотошоп", "другое"]
]

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = {"step": "main_menu", "data": {}}
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Добрый день! Какая услуга вас интересует?", reply_markup=reply_markup)

# Отправка заявки владельцу
async def send_application(user_id, data, context: ContextTypes.DEFAULT_TYPE):
    lines = ["📥 НОВАЯ ЗАЯВКА"]
    lines.append(f"🔹 Услуга: {data.get('услуга', '-')}")
    if "формат" in data:
        lines.append(f"📏 Формат: {data['формат']}")
    if "бумага" in data:
        lines.append(f"📄 Бумага: {data['бумага']}")
    if "примечание" in data:
        lines.append(f"📝 Примечание: {data['примечание']}")
    if "файлы" in data:
        lines.append(f"📎 Прикреплено файлов: {len(data['файлы'])}")    message = "\n".join(lines)
    try:
        await context.bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=message)
    except Exception as e:
        logger.error(f"Ошибка отправки заявки: {e}")

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""
    
    if user_id not in user_sessions:
        return await start(update, context)

    session = user_sessions[user_id]
    step = session["step"]
    data = session["data"]

    # Подтверждение
    if step == "confirmation":
        if any(word in text.lower() for word in ["да", "верно", "отправить"]):
            await send_application(user_id, data, context)
            await update.message.reply_text("✅ Заявка отправлена! Мы свяжемся с вами в ближайшее время.")
            user_sessions.pop(user_id, None)
        elif any(word in text.lower() for word in ["нет", "заново", "начать"]):
            await start(update, context)
        else:
            await update.message.reply_text("Пожалуйста, выберите: ✅ Да, отправить или ↩️ Нет, начать заново.")
        return

    # Выбор услуги
    if step == "main_menu":
        if text.lower() not in [btn.lower() for row in MAIN_MENU for btn in row]:
            await update.message.reply_text("Пожалуйста, выберите услугу из списка.")
            return
        data["услуга"] = text
        service = text.lower()

        if "печать фото" in service:
            kb = [["10×15 (А6)", "15×20 (А5)"], ["21×30 (А4)", "30×42 (А3)"]]
            await update.message.reply_text("Выберите формат:", reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True))
            session["step"] = "photo_format"
        elif "печать документов" in service:
            await update.message.reply_text("Пришлите файлы и укажите: цветная/ч/б печать и количество копий.")
            session["step"] = "docs_info"
        else:
            await update.message.reply_text("Пожалуйста, пришлите файлы или опишите задачу.")
            session["step"] = "other_info"
# Выбор формата фото    elif step == "photo_format":
        if text not in ["10×15 (А6)", "15×20 (А5)", "21×30 (А4)", "30×42 (А3)"]:
            await update.message.reply_text("Пожалуйста, выберите формат из предложенных.")
            return
        data["формат"] = text
        kb = [["глянцевая", "матовая"]]
        await update.message.reply_text("На какой бумаге напечатать?", reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True))
        session["step"] = "photo_paper"

    # Выбор бумаги
    elif step == "photo_paper":
        if text.lower() not in ["глянцевая", "матовая"]:
            await update.message.reply_text("Пожалуйста, выберите: глянцевая или матовая.")
            return
        data["бумага"] = text.lower()
        await update.message.reply_text("Теперь пришлите фотографии для печати.")
        session["step"] = "photo_files"

    # Сбор завершён — показываем подтверждение
    elif step in ["photo_files", "docs_info", "other_info"]:
        if text:
            data["примечание"] = text
        # Формируем сводку
        summary = f"Проверьте ваш заказ:\n\n🔹 Услуга: {data.get('услуга', '-')}"
        if "формат" in data:
            summary += f"\n📏 Формат: {data['формат']}"
        if "бумага" in data:
            summary += f"\n📄 Бумага: {data['бумага']}"
        if "примечание" in data:
            summary += f"\n📝 Примечание: {data['примечание']}"
        if "файлы" in data:
            summary += f"\n📎 Файлов: {len(data['файлы'])}"
        summary += "\n\n---------------------\nВсё верно?"
        kb = [["✅ Да, отправить", "↩️ Нет, начать заново"]]
        await update.message.reply_text(summary, reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True))
        session["step"] = "confirmation"

# Обработка файлов и фото
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
# Запуск бота
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file))
    logger.info("Бот запущен...")
    app.run_polling()

if name == "main":
    main()
