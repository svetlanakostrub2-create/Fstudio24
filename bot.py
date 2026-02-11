import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# === НАСТРОЙКИ ===
BOT_TOKEN = "7978471971:AAGgAFKwEoBCPtxStPCK1aF06Iz7vuoUWQo"  # ← СЮДА ВСТАВЬ ТОКЕН
YOUR_TELEGRAM_ID = 1606381134  # ← СЮДА СВОЙ TELEGRAM ID

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

user_sessions = {}

MAIN_MENU = [
    ["печать фото", "печать документов"],
    ["реставрация фото", "изготовление визиток/буклетов/наклеек"],
    ["оцифровка аудио и видео кассет и фотопленок"],
    ["термопечать на футболках/кружках и тд"],
    ["фотошоп", "другое"]
]

def format_summary( dict) -> str:
    """Формирует красивую сводку для подтверждения"""
    lines = ["Проверьте ваш заказ:"]
    lines.append("🔹 Услуга: " + data.get("услуга", "-"))
    if "формат" in 
        lines.append("📏 Формат: " + data["формат"])
    if "бумага" in 
        lines.append("📄 Бумага: " + data["бумага"])
    if "примечание" in data:
        lines.append("📝 Примечание: " + data["примечание"])
    if "файлы" in data:
        lines.append(f"📎 Файлов: {len(data['файлы'])}")
    lines.append("---------------------")
    lines.append("Всё верно?")
    return "\n".join(lines)

async def send_application(user_id: int,  dict, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет заявку владельцу"""
    lines = ["📥 <b>НОВАЯ ЗАЯВКА</b>"]
    for key, value in data.items():
        if key == "услуга":
            lines.append(f"🔹 Услуга: {value}")
        elif key == "формат":
            lines.append(f"📏 Формат: {value}")
        elif key == "бумага":
            lines.append(f"📄 Бумага: {value}")
        elif key == "цветность_копии":
            lines.append(f"🖨️ Печать: {value}")
        elif key == "примечание":
            lines.append(f"📝 Примечание: {value}")
        elif key == "файлы":
            lines.append(f"📎 Прикреплено файлов: {len(value)}")
    message = "\n".join(lines)
    try:
        await context.bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Не удалось отправить заявку: {e}")
        await context.bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=message.replace("<b>", "").replace("</b>", ""))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = {"step": "main_menu", "data": {}}
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Добрый день! Какая услуга вас интересует?", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""
    
    if user_id not in user_sessions:
        await start(update, context)
        return

    session = user_sessions[user_id]
    step = session["step"]
    data = session["data"]

    # === Подтверждение ===
    if step == "confirmation":
        if "да" in text.lower() or "верно" in text.lower() or "отправить" in text.lower():
            await send_application(user_id, data, context)
            await update.message.reply_text("✅ Заявка отправлена! Мы свяжемся с вами в ближайшее время.")
            user_sessions.pop(user_id, None)
        elif "нет" in text.lower() or "заново" in text.lower():
            await start(update, context)
        else:
            await update.message.reply_text("Пожалуйста, выберите: ✅ Да, отправить или ↩️ Нет, начать заново.")
        return

    # === ШАГ 1: выбор услуги ===
    if step == "main_menu":
        if text.lower() not in [btn.lower() for row in MAIN_MENU for btn in row]:
            await update.message.reply_text("Пожалуйста, выберите услугу из списка.")
            return

        data["услуга"] = text
        service = text.lower()

        if "печать фото" in service:
            keyboard = [["10×15 (А6)", "15×20 (А5)"], ["21×30 (А4)", "30×42 (А3)"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text("Выберите формат фотографии:", reply_markup=reply_markup)
            session["step"] = "photo_format"

        elif "печать документов" in service:
            await update.message.reply_text(
                "Пожалуйста, пришлите файлы для печати и укажите в сообщении:\n"
                "— цветная или ч/б печать\n"
                "— количество копий"
            )
            session["step"] = "docs_info"

        elif "реставрация фото" in service:
            await update.message.reply_text("Пожалуйста, пришлите фотографии, которые нужно реставрировать.")
            session["step"] = "restoration_files"

        elif "визиток" in service or "буклетов" in service or "наклеек" in service:
            await update.message.reply_text(
                "Уточните, что именно вы хотите изготовить (визитки, буклеты, наклейки и т.д.) и пришлите макет или описание."
            )
            session["step"] = "printing_other"

        elif "оцифровка" in service:
            await update.message.reply_text(
                "Уточните, что нужно оцифровать: аудиокассеты, видеокассеты, фотоплёнки? "
                "Если есть — приложите список или фото носителей."
            )
            session["step"] = "digitization_info"

        elif "термопечать" in service:
            await update.message.reply_text(
                "Что вы хотите напечатать? (футболка, кружка, чехол и т.д.)\n"
                "Пришлите изображение и укажите размер/тип изделия."
            )
            session["step"] = "heat_print_info"

        elif "фотошоп" in service:
            await update.message.reply_text("Опишите задачу и пришлите исходные файлы.")
            session["step"] = "photoshop_info"

        elif "другое" in service:
            await update.message.reply_text("Пожалуйста, опишите, какая услуга вам нужна.")
            session["step"] = "other_info"

    # === ШАГ 2: формат фото ===
    elif step == "photo_format":
        if text not in ["10×15 (А6)", "15×20 (А5)", "21×30 (А4)", "30×42 (А3)"]:
            await update.message.reply_text("Пожалуйста, выберите формат из предложенных.")
            return
        data["формат"] = text
        paper_keyboard = [["глянцевая", "матовая"]]
        reply_markup = ReplyKeyboardMarkup(paper_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("На какой бумаге напечатать?", reply_markup=reply_markup)
        session["step"] = "photo_paper"

    # === ШАГ 3: бумага ===
    elif step == "photo_paper":
        if text.lower() not in ["глянцевая", "матовая"]:
            await update.message.reply_text("Пожалуйста, выберите тип бумаги: глянцевая или матовая.")
            return
        data["бумага"] = text.lower()
        await update.message.reply_text("Теперь пришлите фотографии для печати.")
        session["step"] = "photo_files"

    # === ШАГ 4: сбор данных завершён → показываем подтверждение ===
    elif step in ["photo_files", "docs_info", "restoration_files", "printing_other",
                  "digitization_info", "heat_print_info", "photoshop_info", "other_info"]:
        if text:
            data["примечание"] = text
        # Переходим к подтверждению
        summary = format_summary(data)
        confirm_keyboard = [["✅ Да, отправить", "↩️ Нет, начать заново"]]
        reply_markup = ReplyKeyboardMarkup(confirm_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(summary, reply_markup=reply_markup)
        session["step"] = "confirmation"

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_sessions:
        return

    session = user_sessions[user_id]
    if "файлы" not in session["data"]:
        session["data"]["файлы"] = []

    file_id = None
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id

    if file_id:
        session["data"]["файлы"].append(file_id)

    current_step = session["step"]
    if current_step == "photo_files":
        await update.message.reply_text("Фото получено. Если нужно ещё — пришлите. Когда всё готово — напишите «Готово» или любое сообщение.")
    elif current_step == "docs_info":
        await update.message.reply_text("Файл получен. Пожалуйста, укажите: цветная/ч/б печать и количество копий.")
    else:
        await update.message.reply_text("Файл получен. Можете добавить ещё или написать примечание.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file))
    logger.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()