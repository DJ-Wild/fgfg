import os
import json
import threading
from dotenv import load_dotenv
import telebot
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

# Загружаем переменные окружения
load_dotenv()
VK_TOKEN = os.getenv("vk_key")
TG_TOKEN = os.getenv("tg_key")

# Инициализируем ботов
tg_bot = telebot.TeleBot(TG_TOKEN)

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# Получаем ID группы ВК для LongPoll
group_info = vk.groups.getById()
GROUP_ID = group_info[0]['id']
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

# Файл для сохранения связок чатов
LINKS_FILE = "chat_links.json"


def load_links():
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_links(links):
    with open(LINKS_FILE, 'w') as f:
        json.dump(links, f)


# Словарь со связями: {"vk_peer_id": "tg_chat_id"}
vk_to_tg = load_links()


def get_vk_by_tg(tg_id):
    """Ищет привязанный ВК чат по ID Телеграм чата"""
    for vk_id, t_id in vk_to_tg.items():
        if str(t_id) == str(tg_id):
            return int(vk_id)
    return None


# ================= TELEGRAM БОТ =================

@tg_bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'animation'])
def handle_tg_message(message):
    tg_chat_id = str(message.chat.id)
    vk_peer_id = get_vk_by_tg(tg_chat_id)

    if vk_peer_id:
        # Берем текст или подпись к файлу (если это картинка/документ)
        content = message.text or message.caption

        # Если есть текст или подпись (то есть мы не отправляем пустые файлы)
        if content:
            sender_name = message.from_user.first_name
            final_message = f"[{sender_name}]: {content}"

            try:
                vk.messages.send(
                    peer_id=vk_peer_id,
                    random_id=get_random_id(),
                    message=final_message
                )
            except Exception as e:
                print(f"Ошибка отправки в ВК: {e}")


# ================= VK БОТ =================

def vk_listener():
    print("ВК-бот запущен и слушает сообщения...")
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.obj.message
            text = msg.get('text', '')
            peer_id = msg.get('peer_id')
            from_id = msg.get('from_id')

            # Обработка команды .connect
            if text.startswith('.connect '):
                try:
                    tg_chat_id = text.split(' ', 1)[1].strip()

                    # Проверяем доступ ТГ-бота к чату
                    try:
                        tg_bot.get_chat(tg_chat_id)

                        # Если ошибок нет, сохраняем привязку
                        vk_to_tg[str(peer_id)] = str(tg_chat_id)
                        save_links(vk_to_tg)

                        vk.messages.send(
                            peer_id=peer_id,
                            random_id=get_random_id(),
                            message=f"✅ Успешно! Этот чат ВК привязан к Telegram чату {tg_chat_id}."
                        )
                    except Exception:
                        # Сработает, если бота нет в группе или ID неверный
                        vk.messages.send(
                            peer_id=peer_id,
                            random_id=get_random_id(),
                            message="❌ Ошибка! Нет доступа к группе или к сообщениям."
                        )
                except IndexError:
                    vk.messages.send(
                        peer_id=peer_id,
                        random_id=get_random_id(),
                        message="❌ Укажите ID чата. Пример: .connect -100123456789"
                    )

            # Обработка команды .s
            elif text.startswith('.s '):
                content = text.split(' ', 1)[1].strip()
                tg_chat_id = vk_to_tg.get(str(peer_id))

                if tg_chat_id:
                    # Получаем имя отправителя из ВК
                    sender_name = "Пользователь"
                    if from_id > 0:
                        user_info = vk.users.get(user_ids=from_id)[0]
                        sender_name = user_info.get('first_name', 'Пользователь')
                    else:
                        # Если написали от имени другой группы
                        group_info = vk.groups.getById(group_id=abs(from_id))[0]
                        sender_name = group_info.get('name', 'Группа')

                    final_message = f"[{sender_name}]: {content}"

                    try:
                        tg_bot.send_message(chat_id=tg_chat_id, text=final_message)
                    except Exception as e:
                        print(f"Ошибка отправки в ТГ: {e}")


# ================= ЗАПУСК =================

if __name__ == '__main__':
    # Запускаем ВК-слушателя в отдельном потоке
    vk_thread = threading.Thread(target=vk_listener, daemon=True)
    vk_thread.start()

    # Запускаем Телеграм-слушателя в основном потоке
    print("ТГ-бот запущен и слушает сообщения...")
    tg_bot.infinity_polling()
