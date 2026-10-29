import threading
import time

import schedule
import config
import storage
import poll


def _job(bot) -> None:
    poll.send_food_poll_all(bot)

def _close_all_polls(bot):
    for chat_id, chat in storage.chats_state.items():
        if chat.get("poll_message_id"):
            poll.close_poll(bot, chat_id)

def start(bot) -> None:
    schedule.every().day.at(config.DAILY_TIME).do(_job, bot=bot)
    # Новая задача: закрытие в 22:00
    schedule.every().day.at(config.CLOSSE_TIME).do(_close_all_polls, bot=bot)
    def _run():
        while True:
            schedule.run_pending()
            time.sleep(30)

    threading.Thread(target=_run, daemon=True).start()
    print(f"⏰ Планировщик: {config.DAILY_TIME} (кроме субботы)")