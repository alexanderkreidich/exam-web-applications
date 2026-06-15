import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')


def _database_uri():
    # На хостинге адрес БД задаётся переменной окружения; локально — SQLite.
    uri = (os.environ.get('SQLALCHEMY_DATABASE_URI')
           or os.environ.get('DATABASE_URL')
           or os.environ.get('MYSQL_URL'))
    if uri:
        # Приводим схему к драйверу mysql-connector.
        if uri.startswith('mysql://'):
            uri = 'mysql+mysqlconnector://' + uri[len('mysql://'):]
        return uri
    return 'sqlite:///project.db'


# Локальная разработка — SQLite. На хостинге университета можно указать MySQL:
# mysql+mysqlconnector://user:password@std-mysql.ist.mospolytech.ru/db_name
SQLALCHEMY_DATABASE_URI = _database_uri()
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False

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
