import os

# Токен: лучше через переменную окружения, но для теста можно оставить строку
TOKEN = os.getenv("MAX_BOT_TOKEN", "f9LHodD0cOLFlMxRG9oy0VbE7FdimBe7AxtJ85Ns9LzZlfdsjoRDm8fn3fZbPBe3yedf1vD0TnfKx5u4wg_E")

# Твой user_id в MAX
ADMIN_USER_ID = 32836451

# Файл состояния
STATE_FILE = "poll_state.json"
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
# Время ежедневной отправки (формат schedule)
DAILY_TIME = "19:22"
CLOSSE_TIME = "19:24"
# День недели, когда опрос НЕ отправляется (5 = суббота)
SKIP_WEEKDAY = 5

# Допустимые варианты ответов (payload -> человекочитаемый текст)
BREAKFAST_OPTIONS = {
    "breakfast": "🥣 Завтрак",
    "both": "🍲 Завтрак и Обед",
    "none": "🚫 Не ем",
}

MENU_IMAGES = {
    0: ["monday_1.jpg", "monday_2.jpg"],      # понедельник
    1: ["tuesday_1.jpg", "tuesday_2.jpg"],
    2: ["wednesday_1.jpg", "wednesday_2.jpg"],
    3: ["thursday_1.jpg", "thursday_2.jpg"],
    4: ["friday_1.jpg", "friday_2.jpg"],
    5: ["saturday_1.jpg", "saturday_2.jpg"],
}