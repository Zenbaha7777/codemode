from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters, CallbackQueryHandler

# Данные
BOT_TOKEN = '6711911624:AAEERidH6aTP113bsZp1YtncEYYRCAp_9h8'
CHANNEL_ID = '-1002168457258'
LIMIT = 5  # Лимит треков на одного пользователя

# Словарь для хранения количества отправленных треков пользователями
user_track_count = {}

async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "Добро пожаловать в музыкальную шкатулку диджея VINCI ❤️\n"
        "Ближайшее мероприятие \"BAKINSKAYA SUETA | NEW YEAR | DEC 25th\"\n"
        "Отправляй свои треки сюда. (Лимит на 1 пользователя: 5 треков)"
    )
    await update.message.reply_text(welcome_message)

async def handle_audio(update: Update, context: CallbackContext) -> None:
    audio = update.message.audio
    user = update.message.from_user

    if audio:
        user_id = user.id
        
        # Обновляем количество треков для пользователя
        if user_id not in user_track_count:
            user_track_count[user_id] = 0
        
        if user_track_count[user_id] >= LIMIT:
            await update.message.reply_text(f"You have reached the limit of {LIMIT} tracks.")
            return
        
        # Увеличиваем счетчик треков для пользователя
        user_track_count[user_id] += 1

        # Формируем сообщение с информацией о пользователе
        user_info = f"Track from user ID: {user.id}, Username: @{user.username or 'N/A'}"
        message_text = f"{user_info}\n\nFilename: {audio.file_name}"

        # Создаем кнопку
        keyboard = [
            [InlineKeyboardButton("Отлично", callback_data=f"thank_you_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем аудиофайл в канал с кнопкой
        await context.bot.send_audio(
            chat_id=CHANNEL_ID,
            audio=audio.file_id,
            caption=message_text,
            reply_markup=reply_markup
        )

        # Отправляем информацию о лимите
        remaining_limit = LIMIT - user_track_count[user_id]
        await update.message.reply_text(f"Твой трек был успешно отправлен диджею. Если он его заценит, тебе придёт сообщение ❤️\nОставшийся лимит треков: {remaining_limit} треков.")
    else:
        await update.message.reply_text("Please send an audio file.")

async def handle_button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = int(query.data.split("_")[-1])  # Получаем user_id из callback_data

    # Отправляем сообщение пользователю
    remaining_limit = LIMIT - user_track_count.get(user_id, 0)
    message = (
        f"Один из твоих треков заценил диджей! Но какой, ты узнаешь на парти. Дерзай отправлять еще треки, если у тебя еще остался лимит. "
        f"Кстати, у тебя еще лимит в {remaining_limit} треков. ❤️"
    )
    await context.bot.send_message(chat_id=user_id, text=message)

    # Подтверждаем получение нажатия кнопки
    await query.answer()

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(CallbackQueryHandler(handle_button_click, pattern="thank_you_"))

    application.run_polling()

if __name__ == '__main__':
    main()
