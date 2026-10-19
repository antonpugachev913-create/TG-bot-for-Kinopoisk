import json

# Файл для хранения данных
DATA_FILE = "user_data.json"

# Функция для загрузки данных
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": {}}

# Функция для сохранения данных
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Сохранение предпочтений пользователя
def save_user_preferences(user_id, favorite_genre, favorite_movie, preferences):
    data = load_data()
    data["users"][str(user_id)] = {
        "favorite_genre": favorite_genre,
        "favorite_movie": favorite_movie,
        "preferences": preferences,
    }
    save_data(data)
