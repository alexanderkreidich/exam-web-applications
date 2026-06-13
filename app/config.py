import os

SECRET_KEY = 'change-me-in-production'

# Локальная разработка — SQLite. На хостинге университета раскомментировать MySQL.
SQLALCHEMY_DATABASE_URI = 'sqlite:///project.db'
# SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://user:password@std-mysql.ist.mospolytech.ru/db_name'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

# По 10 записей на страницу (требование задания)
PER_PAGE = 10

# Каталог для хранения файлов обложек
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'images')

# Разрешённые HTML-теги при санитизации Markdown-описаний и рецензий
ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr', 'blockquote', 'pre', 'code',
    'strong', 'b', 'em', 'i', 'u', 's', 'del',
    'ul', 'ol', 'li', 'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt', 'title'],
}
