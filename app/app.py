from flask import Flask, send_from_directory
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError

from models import db, Cover
from auth import bp as auth_bp, init_login_manager
from books import bp as books_bp
from reviews import bp as reviews_bp
from commands import init_commands
from tools import render_markdown

app = Flask(__name__)
application = app  # NGINX Unit ожидает объект с именем application

app.config.from_pyfile('config.py')

db.init_app(app)
migrate = Migrate(app, db)
init_login_manager(app)
init_commands(app)


@app.errorhandler(SQLAlchemyError)
def handle_sqlalchemy_error(err):
    error_msg = ('Возникла ошибка при подключении к базе данных. '
                 'Повторите попытку позже.')
    return f'{error_msg} (Подробнее: {err})', 500


app.register_blueprint(auth_bp)
app.register_blueprint(books_bp)
app.register_blueprint(reviews_bp)

# Markdown-описания преобразуются в HTML прямо в шаблонах.
app.jinja_env.filters['markdown'] = render_markdown


@app.route('/covers/<int:cover_id>')
def cover(cover_id):
    img = db.get_or_404(Cover, cover_id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], img.storage_filename)
