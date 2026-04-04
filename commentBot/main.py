import random

from pyrogram import Client, filters
import asyncio

# --- НАСТРОЙКИ ---
API_ID = 36002469  # Ваш API ID
API_HASH = '6b168b27d3fc59a3385023fbea2b2e7a'  # Ваш API HASH
CHAT_ID= "coments2025"
MESSAGES_POOL = [
    "Согласен!",
    "Интересно 🤔",
    "Буду ждать",
    "Записался!",
    "+",
    "Ого, круто",
    "Ждем подробностей"
]
TARGETS = [0, 49, 99]

PROXY = {
    "scheme": "mtproto",
    "hostname": "eu.mt-proxy.org",      # IP адрес прокси
    "port": 443,               # Порт прокси
    "secret": "eec6c206c4d429f36d13af11fbd3c35e786d742d70726f78792e6f7267"  # Секретный хеш (начинается на dd или ee)
}
# -----------------


app = Client(
    "my_account",
    api_id=API_ID,
    api_hash=API_HASH,
    proxy=PROXY
)

# ... (дальше идет основной код логики, который мы написали ранее) ...

state = {
    "last_post_id": None,
    "current_count": 0,
    "sent_targets": set(),
    "available_messages": []
}


def get_random_message():
    if not state["available_messages"]:
        state["available_messages"] = MESSAGES_POOL.copy()
        random.shuffle(state["available_messages"])
    return state["available_messages"].pop()


@app.on_message(filters.chat(CHAT_ID))
async def count_handler(client, message):
    if message.from_user and message.from_user.is_self:
        return

    # 1. Новый пост
    if message.sender_chat and not message.from_user:
        state["last_post_id"] = message.id
        state["current_count"] = 0
        state["sent_targets"] = set()
        print(f"\n[!] Новый пост {message.id}. Мониторинг через MTProto...")

        if 0 in TARGETS:
            await client.send_message(message.chat.id, get_random_message(), reply_to_message_id=message.id)
            state["sent_targets"].add(0)
        return

    # 2. Счетчик
    if state["last_post_id"]:
        state["current_count"] += 1
        print(f"\rКомментариев: {state['current_count']} ", end="")

        for t in TARGETS:
            if t > 0 and state["current_count"] >= t and t not in state["sent_targets"]:
                state["sent_targets"].add(t)
                text = get_random_message()
                await client.send_message(
                    chat_id=message.chat.id,
                    text=text,
                    reply_to_message_id=state["last_post_id"]
                )
                print(f"\n[STRIKE] Цель {t} выполнена! Отправлено: {text}")

        if len(state["sent_targets"]) == len(TARGETS):
            state["last_post_id"] = None


print("Запуск через MTProto...")
app.run()
