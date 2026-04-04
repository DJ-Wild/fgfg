import telebot

# Вставь сюда токен твоего бота, полученный у @BotFather
TOKEN = '8495027021:AAFSoCpT1VYnmcKTB9d6LzuzOu3yr2w0z-Q'
bot = telebot.TeleBot(TOKEN)

# Словари для хранения данных в оперативной памяти.
# Для долгосрочного хранения в будущем можно перевести это в SQLite.
warnings = {}  # Формат: {chat_id: {user_id: count}}
warn_limits = {}  # Формат: {chat_id: limit}
DEFAULT_LIMIT = 3  # Лимит предупреждений по умолчанию


def is_admin(message):
    """Проверяет, является ли пользователь администратором группы."""
    if message.chat.type == 'private':
        bot.reply_to(message, "⚠️ Модераторские команды работают только в группах!")
        return False

    user_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
    return user_status in ['administrator', 'creator']


def extract_reason(text, command):
    """Извлекает причину из текста сообщения."""
    # Убираем саму команду из текста
    args = text.split(maxsplit=1)
    if len(args) > 1:
        return args[1]
    return "Причина не указана"


@bot.message_handler(commands=['set_warn_limit'])
def set_limit(message):
    if not is_admin(message):
        return

    args = message.text.split()
    if len(args) == 2 and args[1].isdigit():
        new_limit = int(args[1])
        warn_limits[message.chat.id] = new_limit
        bot.reply_to(message, f"✅ Лимит предупреждений для этого чата установлен на: <b>{new_limit}</b>",
                     parse_mode='HTML')
    else:
        bot.reply_to(message, "⚠️ Использование: `/set_warn_limit {число}`", parse_mode='Markdown')


@bot.message_handler(commands=['warn'])
def warn_user(message):
    if not is_admin(message):
        return

    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Команда должна быть ответом на сообщение нарушителя!")
        return

    chat_id = message.chat.id
    target_user = message.reply_to_message.from_user

    # Защита от выдачи варна админам и ботам
    target_status = bot.get_chat_member(chat_id, target_user.id).status
    if target_status in ['administrator', 'creator']:
        bot.reply_to(message, "❌ Нельзя выдать предупреждение администратору!")
        return

    reason = extract_reason(message.text, '/warn')

    # Инициализация словарей, если чат или пользователь новые
    if chat_id not in warnings:
        warnings[chat_id] = {}

    current_warns = warnings[chat_id].get(target_user.id, 0) + 1
    warnings[chat_id][target_user.id] = current_warns

    limit = warn_limits.get(chat_id, DEFAULT_LIMIT)

    if current_warns >= limit:
        # Если лимит достигнут — баним
        try:
            bot.ban_chat_member(chat_id, target_user.id)
            warnings[chat_id][target_user.id] = 0  # Сбрасываем варны после бана
            bot.reply_to(message, f"🚫 Пользователь {target_user.first_name} был <b>забанен</b>.\n"
                                  f"Достигнут лимит предупреждений: {current_warns}/{limit}.\n"
                                  f"Причина: {reason}", parse_mode='HTML')
        except Exception as e:
            bot.reply_to(message, "❌ Не удалось забанить пользователя. Проверьте, есть ли у бота права администратора.")
    else:
        bot.reply_to(message,
                     f"⚠️ Пользователь {target_user.first_name} получил предупреждение ({current_warns}/{limit}).\n"
                     f"Причина: {reason}", parse_mode='HTML')


@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not is_admin(message):
        return

    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Команда должна быть ответом на сообщение нарушителя!")
        return

    chat_id = message.chat.id
    target_user = message.reply_to_message.from_user

    if bot.get_chat_member(chat_id, target_user.id).status in ['administrator', 'creator']:
        bot.reply_to(message, "❌ Нельзя забанить администратора!")
        return

    reason = extract_reason(message.text, '/ban')

    try:
        bot.ban_chat_member(chat_id, target_user.id)
        bot.reply_to(message, f"🚫 Пользователь {target_user.first_name} был <b>забанен</b>.\n"
                              f"Причина: {reason}", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка. Проверьте права бота на блокировку пользователей.")


@bot.message_handler(commands=['kick'])
def kick_user(message):
    if not is_admin(message):
        return

    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Команда должна быть ответом на сообщение нарушителя!")
        return

    chat_id = message.chat.id
    target_user = message.reply_to_message.from_user

    if bot.get_chat_member(chat_id, target_user.id).status in ['administrator', 'creator']:
        bot.reply_to(message, "❌ Нельзя кикнуть администратора!")
        return

    reason = extract_reason(message.text, '/kick')

    try:
        # В Telegram нет отдельного метода kick.
        # Кик - это бан и моментальный разбан (чтобы пользователь мог вернуться по ссылке)
        bot.ban_chat_member(chat_id, target_user.id)
        bot.unban_chat_member(chat_id, target_user.id)
        bot.reply_to(message, f"👢 Пользователь {target_user.first_name} был <b>кикнут</b> из чата.\n"
                              f"Причина: {reason}", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, "❌ Ошибка. Проверьте права бота на блокировку пользователей.")


if __name__ == '__main__':
    print("Бот запущен...")
    # none_stop=True предотвращает остановку бота при мелких ошибках сети
    bot.polling(none_stop=True)
