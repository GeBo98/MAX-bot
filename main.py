import config
import storage
import poll
import scheduler
from maxpyin import MaxBot


def _handle_callback(bot, update) -> None:
    cb = update.callback
    if cb is None or cb.user is None:
        return

    msg = update.message
    if msg is None:
        return

    # Определяем chat_id из сообщения, к которому привязана кнопка
    if msg.recipient.chat_type == "dialog":
        return  # опросы только в чатах

    chat_id = msg.recipient.chat_id
    user = cb.user
    user_id = str(user.user_id)
    user_name = getattr(user, "first_name", None) or getattr(user, "username", f"User_{user_id}")

    poll.register_answer(chat_id, user_id, user_name, cb.payload)
    poll.refresh_poll_message(bot, chat_id)
    bot.answer_callback(cb.callback_id, notification="✅ Записано!")


def _handle_admin_command(bot, msg, text_lower: str) -> None:
    parts = text_lower.split(maxsplit=1)
    cmd = parts[0]
    arg = parts[1].strip() if len(parts) > 1 else None

    # /chats разрешаем и в личке
    if cmd == "/chats":
        active = {
            cid: c for cid, c in storage.chats_state.items()
            if c.get("owner_id")
        }
        if not active:
            bot.send_message("📭 Нет активных чатов.", user_id=msg.sender.user_id)
            return

        lines = ["📋 **Активные чаты**", ""]
        for cid, c in active.items():
            # Пытаемся получить название чата
            chat_title = cid  # fallback — ID
            try:
                # Замените get_chat на реальный метод из maxpyin, если он называется иначе
                chat_info = bot.get_chat(int(cid))
                if chat_info and getattr(chat_info, "title", None):
                    chat_title = chat_info.title
            except Exception as e:
                print(f"⚠️ Не удалось получить название для {cid}: {e}")

            owner = c.get("owner_id")
            date = c.get("poll_date") or "—"
            count = len(c.get("responses", {}))
            lines.append(
                f"• **{chat_title}**\n"
                f"  владелец: `{owner}`\n"
                f"  опрос: {date}, ответов: {count}"
            )
        bot.send_message("\n".join(lines), user_id=msg.sender.user_id, text_format="markdown")
        return

    # Команды работают только в групповых чатах
    if msg.recipient.chat_type == "dialog":
        bot.send_message("⚠️ Команды работают только в групповых чатах.", user_id=msg.sender.user_id)
        return

    chat_id = msg.recipient.chat_id
    sender_id = msg.sender.user_id
    chat = storage.get_chat(chat_id)

    if cmd == "/start_poll":
        if chat["owner_id"] is None:
            chat["owner_id"] = sender_id
        elif chat["owner_id"] != sender_id:
            bot.send_message("⚠️ Этот опрос уже ведёт другой администратор.", user_id=sender_id)
            return
        storage.save_state()
        bot.send_message(f"✅ Опрос включён.", chat_id=chat_id, text_format="markdown")

    elif cmd == "/stop_poll":
        if chat["owner_id"] != sender_id:
            bot.send_message("⚠️ Только владелец опроса может его выключить.", user_id=sender_id)
            return
        chat["owner_id"] = None
        storage.save_state()
        bot.send_message("⏸️ Опрос выключен.", chat_id=chat_id)

    elif cmd == "/results":
        if chat["owner_id"] != sender_id:
            bot.send_message("⚠️ Только владелец опроса может смотреть статистику.", user_id=sender_id)
            return
        poll.send_results_to_admin(bot, chat_id, arg)

    elif cmd == "/test_poll":
        if chat["owner_id"] != sender_id:
            return
        poll.send_food_poll_to_chat(bot, chat_id)
        bot.send_message("🧪 Тестовый опрос отправлен.", user_id=sender_id)

def main() -> None:
    print("BOOT: main.py started", flush=True)
    storage.load_state()
    print("BOOT: state loaded", flush=True)
    bot = MaxBot(config.TOKEN, verify=False)
    print("BOOT: bot created", flush=True)

    try:
        scheduler.start(bot)
        print("BOOT: scheduler started", flush=True)
    except Exception as e:
        print(f"BOOT: scheduler error: {e}", flush=True)

    print("🤖 Бот запущен." , flush=True)
    for update in bot.poll(types=["message_created", "message_callback"]):
        print("BOOT: got update", flush=True)
        try:
            if update.update_type == "message_callback":
                _handle_callback(bot, update)
            else:
                msg = update.message
                if msg and msg.body and msg.body.text:
                    sender_id = msg.sender.user_id
                    # Админом может быть любой, кто напишет команду — проверка внутри
                    _handle_admin_command(bot, msg, msg.body.text.strip().lower())
        except Exception as e:
            print(f"❌ Ошибка: {e}")


if __name__ == "__main__":

    main()