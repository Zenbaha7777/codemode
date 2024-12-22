from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters, CallbackQueryHandler

BOT_TOKEN = '6711911624:AAEERidH6aTP113bsZp1YtncEYYRCAp_9h8'
CHANNEL_ID = '-1002168457258'
MAIN_ADMIN_ID = 1996445463
LIMIT = 5
user_track_count, user_custom_limits, admins = {}, {}, {MAIN_ADMIN_ID}
started_users = set()
next_event = "BAKINSKAYA SUETA | NEW YEAR | DEC 25th (Используй /limit чтобы проверить лимит треков!)"
GIF_PATH = 'welcome.gif'  # Замените на путь к вашему локальному GIF-файлу

async def set_bot_commands(app):
    commands = [BotCommand("start", "Начать работу с ботом"), BotCommand("limit", "Проверить лимит треков"), BotCommand("admin", "Войти в админ-панель")]
    await app.bot.set_my_commands(commands)

async def start(update, context):
    user = update.message.from_user
    user_id = user.id
    started_users.add(user_id)
    user_limit = user_custom_limits.get(user_id, LIMIT)

    try:
        with open(GIF_PATH, 'rb') as gif:
            await context.bot.send_animation(
                chat_id=user_id,
                animation=gif,
                caption=(
                    f"Добро пожаловать в музыкальную шкатулку VINCI ❤️\n"
                    f"Ближайшее мероприятие: \"{next_event}\"\n"
                    f"Отправляй свои треки сюда. (Лимит: {user_limit} треков)\n"
                    f"Используй команду /limit для проверки лимита."
                )
            )
    except FileNotFoundError:
        await update.message.reply_text(
            f"Добро пожаловать в музыкальную шкатулку VINCI ❤️\n"
            f"Ближайшее мероприятие: \"{next_event}\"\n"
            f"Отправляй свои треки сюда. (Лимит: {user_limit} треков)\n"
            f"Используй команду /limit для проверки лимита."
        )

async def handle_audio(update, context):
    audio, user = update.message.audio, update.message.from_user
    if not audio: return await update.message.reply_text("Пожалуйста, отправьте аудиофайл.")
    user_id = user.id
    user_limit = user_custom_limits.get(user_id, LIMIT)
    if user_id not in user_track_count: user_track_count[user_id] = 0
    if user_track_count[user_id] >= user_limit: return await update.message.reply_text(f"Лимит в {user_limit} треков достигнут.")
    user_track_count[user_id] += 1
    msg = f"Track from user ID: {user.id}, Username: @{user.username or 'N/A'}\n\nFilename: {audio.file_name}"
    keyboard = [[InlineKeyboardButton("Отлично", callback_data=f"thank_you_{user_id}")]]
    await context.bot.send_audio(CHANNEL_ID, audio=audio.file_id, caption=msg, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text(f"Трек отправлен. Осталось {user_limit - user_track_count[user_id]} треков.")

async def handle_button_click(update, context):
    query, user_id = update.callback_query, int(update.callback_query.data.split("_")[-1])
    remaining_limit = user_custom_limits.get(user_id, LIMIT) - user_track_count.get(user_id, 0)
    msg = f"Один из треков заценён диджеем! Осталось {remaining_limit} треков. ❤️"
    await context.bot.send_message(chat_id=user_id, text=msg)
    await query.answer("Сообщение отправлено!")

async def check_limit(update, context):
    user_id = update.message.from_user.id
    user_limit = user_custom_limits.get(user_id, LIMIT)
    remaining_limit = user_limit - user_track_count.get(user_id, 0)
    await update.message.reply_text(f"Осталось {remaining_limit} треков.")

async def admin_panel(update, context):
    if update.message.from_user.id not in admins:
        return await update.message.reply_text("Нет доступа к этой команде.")
    await show_admin_panel(update, context)

async def show_admin_panel(update, context):
    keyboard = [
        [InlineKeyboardButton("Изменить мероприятие", callback_data="change_event")],
        [InlineKeyboardButton("Добавить администратора", callback_data="add_admin")],
        [InlineKeyboardButton("Установить лимит", callback_data="set_limit")],
        [InlineKeyboardButton("Сбросить лимит пользователя", callback_data="reset_limit")],
        [InlineKeyboardButton("Статистика", callback_data="view_stats")],
        [InlineKeyboardButton("Расссылка", callback_data="broadcast")],
        [InlineKeyboardButton("Показать администраторов", callback_data="view_admins")],
        [InlineKeyboardButton("Удалить администратора", callback_data="remove_admin")]
    ]
    await update.message.reply_text("Админ-панель:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_admin_actions(update, context):
    query, data = update.callback_query, update.callback_query.data
    if data == "change_event":
        context.user_data["awaiting_event"] = True
        await query.message.reply_text("Введите новое мероприятие:")
    elif data == "add_admin":
        context.user_data["awaiting_new_admin"] = True
        await query.message.reply_text("Введите ID нового администратора:")
    elif data == "set_limit":
        context.user_data["awaiting_set_limit"] = True
        await query.message.reply_text("Введите ID пользователя и новый лимит через пробел:")
    elif data == "reset_limit":
        context.user_data["awaiting_reset_limit"] = True
        await query.message.reply_text("Введите ID пользователя для сброса лимита:")
    elif data == "view_stats":
        total_users = len(started_users)
        await query.message.reply_text(f"Пользователей запустивших бота: {total_users}")
    elif data == "broadcast":
        context.user_data["awaiting_broadcast"] = True
        await query.message.reply_text("Введите сообщение для рассылки:")
    elif data == "view_admins":
        await query.message.reply_text(f"Администраторы:\n{', '.join(map(str, admins))}")
    elif data == "remove_admin":
        context.user_data["awaiting_remove_admin"] = True
        await query.message.reply_text("Введите ID администратора для удаления:")
    await query.answer()

async def handle_text_input(update, context):
    if context.user_data.get("awaiting_event"):
        global next_event
        next_event = update.message.text
        context.user_data["awaiting_event"] = False
        await update.message.reply_text(f"Мероприятие обновлено: {next_event}")
    elif context.user_data.get("awaiting_new_admin"):
        try:
            new_admin_id = int(update.message.text)
            admins.add(new_admin_id)
            context.user_data["awaiting_new_admin"] = False
            await update.message.reply_text(f"Добавлен администратор: {new_admin_id}")
        except ValueError:
            await update.message.reply_text("Неверный ID.")
    elif context.user_data.get("awaiting_remove_admin"):
        try:
            remove_admin_id = int(update.message.text)
            if remove_admin_id in admins:
                admins.remove(remove_admin_id)
                await update.message.reply_text(f"Администратор {remove_admin_id} удалён.")
            else:
                await update.message.reply_text("ID не найден среди администраторов.")
            context.user_data["awaiting_remove_admin"] = False
        except ValueError:
            await update.message.reply_text("Неверный ID.")
    elif context.user_data.get("awaiting_reset_limit"):
        try:
            reset_user_id = int(update.message.text)
            if reset_user_id in user_track_count:
                user_track_count[reset_user_id] = 0
                await update.message.reply_text(f"Лимит пользователя {reset_user_id} сброшен.")
            else:
                await update.message.reply_text(f"ID {reset_user_id} не найден в списке пользователей.")
            context.user_data["awaiting_reset_limit"] = False
        except ValueError:
            await update.message.reply_text("Неверный ID.")
    elif context.user_data.get("awaiting_set_limit"):
        try:
            user_id, new_limit = map(int, update.message.text.split())
            user_custom_limits[user_id] = new_limit
            context.user_data["awaiting_set_limit"] = False
            await update.message.reply_text(f"Для пользователя {user_id} установлен новый лимит: {new_limit}.")
        except ValueError:
            await update.message.reply_text("Введите ID пользователя и новый лимит через пробел.")
    elif context.user_data.get("awaiting_broadcast"):
        message = update.message.text
        for user_id in started_users:
            try:
                await context.bot.send_message(chat_id=user_id, text=message)
            except Exception:
                continue
        context.user_data["awaiting_broadcast"] = False
        await update.message.reply_text("Рассылка завершена.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(CommandHandler("limit", check_limit))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(handle_button_click, pattern="thank_you_"))
    application.add_handler(CallbackQueryHandler(handle_admin_actions, pattern="change_event|add_admin|set_limit|reset_limit|view_stats|broadcast|view_admins|remove_admin"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    application.run_polling()

if __name__ == "__main__":
    main()
