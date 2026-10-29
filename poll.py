from datetime import datetime, timedelta

import os
import config
import storage
from maxpyin import InlineKeyboard, CallbackButton


def _get_menu_image() -> str | None:
    """Возвращает путь к картинке меню на сегодня (2-недельный цикл)."""
    now = datetime.now() + timedelta(days=1)   # ← завтра
    weekday = now.weekday()
    if weekday not in config.MENU_IMAGES:
        return None
    week_parity = now.isocalendar().week % 2
    images = config.MENU_IMAGES[weekday]
    filename = images[week_parity] if week_parity < len(images) else images[0]
    # Возвращаем полный путь относительно папки бота
    return os.path.join(config.IMAGES_DIR, filename)

def _build_keyboard() -> InlineKeyboard:
    kb = InlineKeyboard()
    for payload, title in config.BREAKFAST_OPTIONS.items():
        kb.add(CallbackButton(text=title, payload=payload))
    return kb


def _build_poll_text(chat_id: str, with_answers: bool = False) -> str:
    chat = storage.get_chat(chat_id)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    lines = [f"🍽️ **Опрос по питанию — {tomorrow}**", "", "Кто будет кушать?"]

    if with_answers and chat["responses"]:
        lines.append("")
        for uid, data in chat["responses"].items():
            name = data.get("name", uid)
            raw = data.get("breakfast", "—")
            answer = config.BREAKFAST_OPTIONS.get(raw, raw)
            lines.append(f"• {name}: {answer}")

    return "\n".join(lines)


def send_food_poll_to_chat(bot, chat_id: str) -> None:
    """Отправляет опрос в конкретный чат (без проверки флага — его проверяет вызывающий)."""
    if datetime.now().weekday() == config.SKIP_WEEKDAY:
        print(f"📅 {chat_id}: суббота, пропускаем.")
        return

    date = storage.start_new_poll_group(chat_id)
    image_path = _get_menu_image()  # получаем путь к картинке

    attachments = []
    if image_path:
        try:
            uploaded = bot.upload_media("image", image_path)
            attachments.append(uploaded.as_attachment("image"))
        except Exception as e:
            print(f"⚠️ {chat_id}: не удалось загрузить картинку {image_path}: {e}")

    attachments.append(_build_keyboard())

    try:
        sent = bot.send_message(
            _build_poll_text(chat_id),
            chat_id=int(chat_id),
            attachments=attachments,
            text_format="markdown",
        )
        chat = storage.get_chat(chat_id)
        chat["poll_message_id"] = sent.body.mid
        storage.save_state()
        print(f"✅ {chat_id}: опрос за {date} отправлен, msg_id={sent.body.mid}")
    except Exception as e:
        print(f"❌ {chat_id}: ошибка отправки: {e}")


def send_food_poll_all(bot) -> None:
    """Ежедневная рассылка во все чаты, где опрос включён (есть owner_id)."""
    for chat_id, chat in storage.chats_state.items():
        if chat.get("owner_id"):
            send_food_poll_to_chat(bot, chat_id)


def refresh_poll_message(bot, chat_id: str) -> None:
    chat = storage.get_chat(chat_id)
    msg_id = chat.get("poll_message_id")
    if not msg_id:
        return

    attachments = []
    image_path = _get_menu_image()
    if image_path:
        try:
            uploaded = bot.upload_media("image", image_path)
            attachments.append(uploaded.as_attachment("image"))
        except Exception as e:
            print(f"⚠️ {chat_id}: не удалось загрузить картинку: {e}")

    attachments.append(_build_keyboard())

    try:
        bot.edit_message(
            msg_id,
            text=_build_poll_text(chat_id, with_answers=True),
            attachments=attachments,
            text_format="markdown",
        )
    except Exception as e:
        print(f"⚠️ {chat_id}: не удалось обновить: {e}")


def close_poll(bot, chat_id: str) -> None:
    """Закрывает опрос: убирает кнопки, оставляя текст и картинку."""
    chat = storage.get_chat(chat_id)
    msg_id = chat.get("poll_message_id")
    if not msg_id:
        return
    
    final_text = _build_poll_text(chat_id, with_answers=True)
    final_text += "\n\n⏰ **Голосование завершено.**"
    
    # Заново собираем вложения: только картинка, без клавиатуры
    attachments = []
    image_path = _get_menu_image()
    if image_path:
        try:
            uploaded = bot.upload_media("image", image_path)
            attachments.append(uploaded.as_attachment("image"))
        except Exception as e:
            print(f"⚠️ {chat_id}: не удалось загрузить картинку при закрытии: {e}")
    
    try:
        # Передаем attachments с картинкой (если она есть). Кнопок тут нет.
        bot.edit_message(
            msg_id,
            text=final_text,
            attachments=attachments, # Список только с картинкой (или пустой, если картинки не было)
            text_format="markdown"
        )
        print(f"✅ {chat_id}: опрос закрыт, кнопки убраны, картинка сохранена.")
    except Exception as e:
        print(f"❌ {chat_id}: ошибка закрытия опроса: {e}")


def register_answer(chat_id: str, user_id: str, user_name: str, payload: str) -> None:
    storage.add_response(chat_id, user_id, user_name, payload)


def send_results_to_admin(bot, chat_id: str, arg: str | None = None) -> None:
    """Отправляет статистику только владельцу этого чата."""
    chat = storage.get_chat(chat_id)
    owner_id = chat.get("owner_id")
    if not owner_id:
        return

    arg = (arg or "today").lower()
    responses = chat.get("responses", {})

    if not responses:
        bot.send_message(f"📭 В чате `{chat_id}` пока нет ответов.", user_id=owner_id, text_format="markdown")
        return

    lines = [f"📊 **Результаты чата** `{chat_id}`", ""]

    if arg == "today":
        lines.append(f"Дата: {chat.get('poll_date', '—')}")
        for uid, data in responses.items():
            name = data.get("name", uid)
            raw = data.get("breakfast", "—")
            answer = config.BREAKFAST_OPTIONS.get(raw, raw)
            lines.append(f"👤 {name}: {answer}")
    else:
        lines.append("(детализация по датам доступна только для текущего опроса)")

    bot.send_message("\n".join(lines), user_id=owner_id, text_format="markdown")