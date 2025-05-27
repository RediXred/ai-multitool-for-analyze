import json
import logging
import os
import asyncio
from threading import Thread
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from asgiref.sync import sync_to_async
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from analysis.models import UploadedFile

# Настройка логов
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
USERNAME, PASSWORD = range(2)

MAIN_MENU = 3
FILE_ACTIONS = 4

# Глобальные переменные для управления event loop
application = None
loop = None

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📁 Мои файлы", callback_data="list_files"),
            InlineKeyboardButton("📤 Загрузить файл", callback_data="upload_file")
        ],
        [InlineKeyboardButton("🚪 Выйти", callback_data="logout")]
    ])

def file_actions_keyboard(file_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_{file_id}"),
            InlineKeyboardButton("🔍 Обновить", callback_data=f"analyze_{file_id}")
        ],
        [InlineKeyboardButton("📊 Подробный отчёт", url=f"{os.getenv('HOST')}/analyze/{file_id}/")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
    ])

def setup_bot():
    """Инициализация и запуск бота в отдельном потоке"""
    global application, loop
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    
    login_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(login_start, pattern="^login$")],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
            MAIN_MENU: [CallbackQueryHandler(handle_main_menu)],
            FILE_ACTIONS: [CallbackQueryHandler(handle_file_actions)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(login_conv)
    
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_error_handler(error_handler)

    # Запуск бота
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())
    loop.run_forever()

# Запускаем бота в отдельном потоке при старте Django
bot_thread = Thread(target=setup_bot, daemon=True)
bot_thread.start()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Вход", callback_data="login"),
            InlineKeyboardButton("Регистрация", url=f"{os.getenv('HOST')}/accounts/register/"),
        ]
    ]
    await update.message.reply_text(
        "Добро пожаловать в AI-Multitool-Analyse Bot! Войдите или зарегистрируйтесь:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Логика логина
async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Пожалуйста, введите ваше имя пользователя:")
    return USERNAME

async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["username"] = update.message.text
    await update.message.reply_text("Теперь введите ваш пароль:")
    return PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from django.contrib.auth import authenticate
    username = context.user_data.get("username")
    password = update.message.text

    # Логирование введённых данных для отладки
    logger.debug(f"Attempting auth for: {username}, pass: {password}")

    try:
        # Правильное асинхронное выполнение
        user = await sync_to_async(authenticate)(
            username=username,
            password=password
        )

        if user:
            context.user_data["django_user"] = user
            logger.info(f"Successful login: {username}")
            await update.message.reply_text(f"✅ Вы вошли как {user.username}!", reply_markup=main_menu_keyboard())
            return MAIN_MENU
        else:
            logger.warning(f"Auth failed for: {username}")
            await update.message.reply_text("❌ Неверные данные. Проверьте логин/пароль и попробуйте снова.")
            return ConversationHandler.END

    except Exception as e:
        logger.error(f"Auth error: {str(e)}", exc_info=True)
        await update.message.reply_text("⚠️ Ошибка сервера. Попробуйте позже.")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Логин отменён.")
    return ConversationHandler.END

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "list_files":
        user = context.user_data["django_user"]
        files = await sync_to_async(list)(user.uploaded_files.all().order_by('-uploaded_at'))
        
        if not files:
            await query.edit_message_text("📂 У вас пока нет загруженных файлов", reply_markup=main_menu_keyboard())
            return MAIN_MENU
        
        # Создаем клавиатуру с файлами
        keyboard = []
        for file in files:
            keyboard.append([
                InlineKeyboardButton(
                    f"📄 {file.filename()}",
                    callback_data=f"file_{file.id}"
                )
            ])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")])
        
        await query.edit_message_text(
            "📂 Выберите файл:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return FILE_ACTIONS
    
    elif query.data == "upload_file":
        await query.edit_message_text("📤 Отправьте файл для анализа")
        return MAIN_MENU
    
    elif query.data == "logout":
        # Выход из системы
        del context.user_data["django_user"]
        await query.edit_message_text("🚪 Вы успешно вышли из системы")
        return ConversationHandler.END

async def delete_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, file_id: int):
    query = update.callback_query
    user = context.user_data["django_user"]
    
    try:
        # Асинхронное получение файла с проверкой существования
        file = await sync_to_async(UploadedFile.objects.get)(id=file_id)
        
        # Асинхронная проверка прав доступа
        is_owner = await sync_to_async(lambda: file.user.id == user.id)()
        if not is_owner:
            logger.warning(f"User {user.id} attempted unauthorized deletion of file {file_id}")
            await query.answer("🚫 Доступ запрещён!")
            return FILE_ACTIONS

        # Асинхронное удаление файла и записи
        file_path = file.file.path
        if await sync_to_async(os.path.exists)(file_path):
            await sync_to_async(os.remove)(file_path)
            
        await sync_to_async(file.delete)()
        
        # Логирование и ответ пользователю
        logger.info(f"File {file_id} deleted by {user.username}")
        await query.edit_message_text(
            f"🗑️ Файл {file.filename()} успешно удалён!",
            reply_markup=main_menu_keyboard()
        )
        return MAIN_MENU

    except UploadedFile.DoesNotExist:
        logger.error(f"File {file_id} not found")
        await query.answer("❌ Файл не найден!")
        return FILE_ACTIONS
        
    except Exception as e:
        logger.error(f"File deletion error: {str(e)}", exc_info=True)
        await query.answer("⛔ Ошибка при удалении!")
        return FILE_ACTIONS

def generate_analysis_report(file):
    report = [
        f"*📄 {file.filename()}*",
        f"_Загружен: {file.uploaded_at.strftime('%d.%m.%Y %H:%M')}_\n",
        "🔍 *Состояние анализов:*",
        f"- VirusTotal: {file.vt_status}",
        f"- AI Анализ: {file.ai_status}"
    ]
    
    if file.vt_result:
        positives = file.vt_result.get('positives', 0)
        report.extend([
            "\n🛡 *VirusTotal:*",
            f"Обнаружений: {positives}",
            "⚠️ Файл помечен как опасный!" if positives > 0 else ""
        ])
    
    if file.ai_result:
        if isinstance(file.ai_result, str):
            import json
            try:
                ai_result_dict = json.loads(file.ai_result)
            except json.JSONDecodeError:
                ai_result_dict = {}
        else:
            ai_result_dict = file.ai_result

        if ai_result_dict:
            report.append("\n🤖 *AI Анализ:*")
            for key, value in ai_result_dict.items():
                report.append(f"*{key}:* {value}")
    
    return "\n".join(report)

async def analyze_file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, file_id: int):
    query = update.callback_query
    user = context.user_data["django_user"]
    
    try:
        # Асинхронное получение файла
        file = await sync_to_async(UploadedFile.objects.get)(id=file_id)
        
        # Асинхронная проверка владельца файла
        is_owner = await sync_to_async(lambda: file.user == user)()
        if not is_owner:
            await query.answer("❌ Ошибка доступа!")
            return FILE_ACTIONS
        
        # Асинхронная генерация отчёта
        analysis_text = await sync_to_async(generate_analysis_report)(file)
        
        await query.edit_message_text(
            analysis_text,
            parse_mode='Markdown',
            reply_markup=file_actions_keyboard(file_id)
        )
        return FILE_ACTIONS
    
    except UploadedFile.DoesNotExist:
        logger.error(f"File {file_id} not found")
        await query.answer("❌ Файл не найден!")
        return FILE_ACTIONS
    except Exception as e:
        logger.error(f"Error analyzing file: {str(e)}", exc_info=True)
        await query.answer("❌ Ошибка анализа!")
        return FILE_ACTIONS

async def handle_file_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("file_"):
        file_id = query.data.split("_")[1]
        context.user_data["selected_file"] = file_id
        await query.edit_message_text(
            "Выберите действие:",
            reply_markup=file_actions_keyboard(file_id)
        )
        return FILE_ACTIONS
    
    elif query.data.startswith("delete_"):
        file_id = query.data.split("_")[1]
        return await delete_file_handler(update, context, file_id)
    
    elif query.data.startswith("analyze_"):
        file_id = query.data.split("_")[1]
        return await analyze_file_handler(update, context, file_id)
    
    elif query.data == "back_to_list":
        return await handle_main_menu(update, context)
    
    elif query.data == "back_to_menu":
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=main_menu_keyboard()
        )
        return MAIN_MENU

# Обработка файлов
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = context.user_data.get("django_user")
    if not user:
        await update.message.reply_text("Сначала войдите через /start → Вход.")
        return

    doc = update.message.document
    if not doc:
        await update.message.reply_text("Пожалуйста, отправьте файл.")
        return

    tg_file = await doc.get_file()
    logger.warning(f"Userid: {user.id}")
    user_dir = os.path.join("media", "uploads", f"user_{str(user.id)}")
    os.makedirs(user_dir, exist_ok=True)
    path = os.path.join(user_dir, doc.file_name)
    await tg_file.download_to_drive(path)

    user_dir = os.path.join("uploads", f"user_{str(user.id)}")
    path = os.path.join(user_dir, doc.file_name)
    uploaded = await sync_to_async(UploadedFile.objects.create)(
        user=user,
        file=path,
        vt_status="not_started",
        ai_status="not_started",
    )
    from analysis.tasks import analyze_uploaded_file
    #analyze_uploaded_file.delay(uploaded.id)

    from analysis.tasks import analyze_file_task
    #analyze_file(uploaded.id)

    from celery import chain

    chain(
        analyze_uploaded_file.s(uploaded.id),
        analyze_file_task.s()
    ).apply_async()

    await update.message.reply_text(f"Файл «{doc.file_name}» загружен, анализ запущен.", reply_markup=main_menu_keyboard())
    return MAIN_MENU

# Обработчик ошибок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Error handling update:", exc_info=context.error)
    if update and hasattr(update, "effective_message"):
        await update.effective_message.reply_text("Произошла ошибка, попробуйте ещё раз.")

# Webhook view
@csrf_exempt
def webhook(request):
    if request.method == "POST":
        try:
            update = Update.de_json(json.loads(request.body), application.bot)
            asyncio.run_coroutine_threadsafe(
                application.process_update(update),
                loop
            )
            return HttpResponse("OK", status=200)
        except Exception as e:
            logger.error("Error processing update:", exc_info=True)
            return HttpResponse(status=500)
    return HttpResponse(status=400)