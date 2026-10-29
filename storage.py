import json
import os
from datetime import datetime

import config

chats_state: dict = {}


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_chat(chat_id) -> dict:
    key = str(chat_id)   # всегда строка
    return chats_state.setdefault(key, {
        "owner_id": None,
        "poll_message_id": None,
        "poll_date": None,
        "responses": {},
    })


def load_state() -> None:
    global chats_state
    if not os.path.exists(config.STATE_FILE):
        return
    try:
        with open(config.STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        chats_state = data.get("chats", {})
        print(f"📂 Загружено чатов: {len(chats_state)}")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки: {e}")


def save_state() -> None:
    try:
        with open(config.STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"chats": chats_state}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения: {e}")


def start_new_poll_group(chat_id: str) -> str:
    """Начинает новую группу ответов на сегодня для конкретного чата."""
    chat = get_chat(chat_id)
    chat["poll_date"] = today_str()
    chat["responses"] = {}  # очищаем ответы прошлого опроса
    save_state()
    return chat["poll_date"]


def add_response(chat_id: str, user_id: str, user_name: str, payload: str) -> None:
    chat = get_chat(chat_id)
    if chat["poll_date"] is None:
        chat["poll_date"] = today_str()
    chat["responses"][user_id] = {"name": user_name, "breakfast": payload}
    save_state()


def is_owner(chat_id: str, user_id: int) -> bool:
    chat = get_chat(chat_id)
    return chat["owner_id"] == user_id