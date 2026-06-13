from flask import (
    Blueprint, render_template, request, current_app,
)

from models import db, Book, Genre
from tools import BooksFilter

bp = Blueprint('books', __name__)


def search_params():
    """Извлекает параметры формы поиска (вариант 3) из query string."""
    return {
        'title': request.args.get('title', '').strip() or None,
        'author': request.args.get('author', '').strip() or None,
        'genre_ids': [int(x) for x in request.args.getlist('genre_ids') if x],
        'years': [int(x) for x in request.args.getlist('years') if x],
        'pages_from': request.args.get('pages_from', type=int),
        'pages_to': request.args.get('pages_to', type=int),
    }


@bp.route('/')
def index():
    params = search_params()
    query = BooksFilter(**params).perform()
    pagination = db.paginate(query, per_page=current_app.config['PER_PAGE'])

    genres = db.session.execute(db.select(Genre).order_by(Genre.name)).scalars().all()
    years = db.session.execute(
        db.select(Book.year).distinct().order_by(Book.year.desc())).scalars().all()

    return render_template(
        'index.html',
        pagination=pagination,
        books=pagination.items,
        genres=genres,
        years=years,
        search_params=params,
    )


@bp.route('/books/<int:book_id>')
def show(book_id):
    book = db.get_or_404(Book, book_id)
    return render_template('books/show.html', book=book)


# --- CRUD книг и рецензии реализуются в следующих коммитах ---
# Маршруты ниже зарегистрированы заранее, чтобы url_for в шаблонах разрешался.

@bp.route('/books/new')
def new():
    return render_template('books/new.html', book=Book(), genres=[], selected_genres=[])


@bp.route('/books', methods=['POST'])
def create():
    return ('Not implemented', 501)


@bp.route('/books/<int:book_id>/edit')
def edit(book_id):
    book = db.get_or_404(Book, book_id)
    return render_template('books/edit.html', book=book)


@bp.route('/books/<int:book_id>', methods=['POST'])
def update(book_id):
    return ('Not implemented', 501)


@bp.route('/books/<int:book_id>/delete', methods=['POST'])
def delete(book_id):
    return ('Not implemented', 501)
