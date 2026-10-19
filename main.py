import telebot
import requests
from telebot import TeleBot

API_TOKEN = "JA9EH58-VEM4V3C-J4H4SZ6-XDZW9GH"
API_URL= "https://api.kinopoisk.dev/v1.4/movie/search"
bot = telebot.TeleBot("8351519692:AAGxyTMoBCAPeZPgjquo-UlUROkuduzDtMc")

# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start_command(message):
    welcome_text = (
        "Привет! 👋 Я бот, который поможет тебе выбрать фильм для просмотра. "
        "Напиши название фильма, чтобы узнать о нем больше, или укажи жанр, чтобы получить рекомендации. "
        "Попробуй команду /help, чтобы увидеть все мои возможности!")

    bot.send_message(message.chat.id, welcome_text)
# Обработчик команды /info
@bot.message_handler(commands=["help"])
def info_command(message):
    info_text = (
        "Я бот, созданный для помощи в выборе фильмов. 🎬\n\n"
        "Основные функции:\n"
        "- Рекомендации по жанрам\n"
        "- Описание фильмов\n"
        "- Помощь в выборе, что посмотреть сегодня.\n\n"

    )
    bot.send_message(message.chat.id, info_text)

    @bot.message_handler(content_types=["text"])
    def handle_text(message):
        """
        Функция обрабатывает текстовые сообщения, предполагая, что пользователь ввел название фильма.
        """
        film_name = message.text.strip()

        # СТРОГАЯ ЗАЩИТА: Если текст совпадает с пунктами меню, мы его НЕ отправляем в Кинопоиск
        if film_name.startswith("/") or "Рекомендации" in film_name or "Описание" in film_name:
            return

        # Уведомляем пользователя, что начался поиск
        bot.send_message(message.chat.id, f"🔍 Ищу информацию о фильме: {film_name}...")

        # Подготовка заголовков для запроса к API Кинопоиска
        headers = {"X-API-KEY": API_TOKEN}
        # Параметры запроса
        params = {"page": 1, "limit": 1, "query": film_name}

        try:
            response = requests.get(API_URL, headers=headers, params=params)

            # Проверяем статус ответа
            if response.status_code == 200:
                data = response.json()
                docs = data.get("docs", [])

                if docs:
                    film = docs[0]
                    film_info = (
                        f"🎬 {film.get('name')}\n"
                        f"📅 Год: {film.get('year')}\n"
                        f"⭐ Рейтинг: {film.get('rating', {}).get('kp')}\n"
                        f"📖 Описание: {film.get('description')}\n"
                        f"🎭 Жанр: {', '.join(genre['name'] for genre in film.get('genres', []))}\n"
                        f"🌍 Страна: {', '.join(country['name'] for country in film.get('countries', []))}\n"
                    )
                    bot.send_message(message.chat.id, film_info, parse_mode="HTML")
                else:
                    bot.send_message(
                        message.chat.id,
                        "😞 К сожалению, я не нашел информации о фильме. Попробуй уточнить название."
                    )
            else:
                # Выводим код ошибки в чат, чтобы точно знать, что не так с токеном
                bot.send_message(
                    message.chat.id,
                    f"⚠️ Ошибка при запросе к API. Код ответа сервера: {response.status_code}. Попробуй позже."
                )
        except Exception as e:
            print(f"Ошибка: {e}")


# Запуск бота
# Состояния для команды /set_preferences
STATE_WAITING_FOR_GENRE = 1
STATE_WAITING_FOR_MOVIE = 2
STATE_WAITING_FOR_ADDITIONAL = 3

# Словарь для отслеживания состояния пользователя
user_states = {}
@bot.message_handler(commands=["set_preferences"])
def set_preferences_command(message):
    """
    Начало ввода предпочтений пользователя.
    """
    bot.send_message(
        message.chat.id,
        "📝 Давайте заполним ваши предпочтения! Какой ваш любимый жанр? 🎭"
    )
    user_states[message.chat.id] = STATE_WAITING_FOR_GENRE
@bot.message_handler(func=lambda message: message.chat.id in user_states)
def handle_preferences(message):
    """
    Обработка шагов для команды /set_preferences.
    """
    state = user_states.get(message.chat.id)

    try:
        if state == STATE_WAITING_FOR_GENRE:
            # Сохранение жанра и запрос следующего шага
            bot.send_message(
                message.chat.id, "Какой ваш любимый фильм? 🎥"
            )
            user_states[message.chat.id] = {
                "state": STATE_WAITING_FOR_MOVIE,
                "favorite_genre": message.text.strip(),
            }

        elif state.get("state") == STATE_WAITING_FOR_MOVIE:
            # Сохранение фильма и запрос следующего шага
            bot.send_message(
                message.chat.id, "Есть ли дополнительные пожелания? Например, актеры, эпоха или что-то другое. 📝"
            )
            user_states[message.chat.id] = {
                "state": STATE_WAITING_FOR_ADDITIONAL,
                "favorite_genre": state["favorite_genre"],
                "favorite_movie": message.text.strip(),
            }

        elif state.get("state") == STATE_WAITING_FOR_ADDITIONAL:
            # Сохранение дополнительных пожеланий и завершение ввода
            favorite_genre = state["favorite_genre"]
            favorite_movie = state["favorite_movie"]
            preferences = message.text.strip()

            # Сохранение данных в файл
            save_user_preferences(
                message.chat.id, favorite_genre, favorite_movie, preferences
            )
            bot.send_message(
                message.chat.id,
                "✅ Ваши предпочтения сохранены! Спасибо, что заполнили их. 🎉",
            )
            del user_states[message.chat.id]  # Удаляем состояние пользователя
    except Exception as e:
        # Обработка ошибок
        bot.send_message(
            message.chat.id,
            "⚠️ Произошла ошибка при обработке вашего ввода. Попробуйте еще раз. Если ошибка повторяется, обратитесь к администратору."
        )
        print(f"Error: {e}")  # Логируем ошибку
def get_movie_recommendations(genre):
    """
    Получение рекомендаций фильмов по жанру через API.
    """
    try:
        response = requests.get(
            API_URL,
            params={"query": genre},
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        if response.status_code == 200:
            data = response.json()
            # Возвращаем список фильмов (например, первые 5)
            return [movie["name"] for movie in data["docs"][:5]]
        else:
            print(f"API error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Request error: {e}")
        return []
@bot.message_handler(commands=["recommend_movie"])
def recommend_movie_command(message):
    """
    Подбор фильма по предпочтениям пользователя.
    """
    user_id = message.chat.id
    data = load_data()

    # Проверяем, есть ли данные о пользователе
    if str(user_id) in data["users"]:
        user_preferences = data["users"][str(user_id)]
        favorite_genre = user_preferences.get("favorite_genre", "")

        if not favorite_genre:
            bot.send_message(
                user_id,
                "🎭 У вас не указан любимый жанр. Попробуйте сначала задать предпочтения с помощью команды /set_preferences."
            )
            return

        # Получаем рекомендации фильмов
        movies = get_movie_recommendations(favorite_genre)

        if movies:
            movie_list = "\n".join([f"• {movie}" for movie in movies])
            bot.send_message(
                user_id,
                f"🎬 Вот несколько фильмов, которые могут вам понравиться:\n{movie_list}"
            )
        else:
            bot.send_message(
                user_id,
                "⚠️ К сожалению, не удалось найти фильмы по вашему запросу. Попробуйте позже."
            )
    else:
        bot.send_message(
            user_id,
            "🔍 У нас нет данных о ваших предпочтениях. Пожалуйста, задайте их с помощью команды /set_preferences."
        )
bot.polling()