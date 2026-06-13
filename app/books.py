from flask import (
    Blueprint, render_template, request, current_app, flash, redirect, url_for,
)
from sqlalchemy.exc import SQLAlchemyError

from models import db, Book, Genre
from tools import BooksFilter, ImageSaver, sanitize_markdown
from auth import rights_required

bp = Blueprint('books', __name__)

SAVE_ERROR = ('При сохранении данных возникла ошибка. '
              'Проверьте корректность введённых данных.')


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


def all_genres():
    return db.session.execute(db.select(Genre).order_by(Genre.name)).scalars().all()


def book_form_params():
    """Заполняет поля книги из формы. Возвращает (book, selected_genre_ids)."""
    book = Book(
        title=request.form.get('title', '').strip(),
        short_desc=sanitize_markdown(request.form.get('short_desc')),
        publisher=request.form.get('publisher', '').strip(),
        author=request.form.get('author', '').strip(),
        year=request.form.get('year', type=int),
        pages=request.form.get('pages', type=int),
    )
    selected_genre_ids = [int(x) for x in request.form.getlist('genre_ids') if x]
    return book, selected_genre_ids


def apply_form(book):
    """Переносит данные формы в существующий объект книги."""
    book.title = request.form.get('title', '').strip()
    book.short_desc = sanitize_markdown(request.form.get('short_desc'))
    book.publisher = request.form.get('publisher', '').strip()
    book.author = request.form.get('author', '').strip()
    book.year = request.form.get('year', type=int)
    book.pages = request.form.get('pages', type=int)
    genre_ids = [int(x) for x in request.form.getlist('genre_ids') if x]
    book.genres = db.session.execute(
        db.select(Genre).where(Genre.id.in_(genre_ids))).scalars().all() if genre_ids else []
    return genre_ids


@bp.route('/')
def index():
    params = search_params()
    query = BooksFilter(**params).perform()
    pagination = db.paginate(query, per_page=current_app.config['PER_PAGE'])

    years = db.session.execute(
        db.select(Book.year).distinct().order_by(Book.year.desc())).scalars().all()

    return render_template(
        'index.html',
        pagination=pagination,
        books=pagination.items,
        genres=all_genres(),
        years=years,
        search_params=params,
    )


@bp.route('/books/<int:book_id>')
def show(book_id):
    book = db.get_or_404(Book, book_id)
    return render_template('books/show.html', book=book)


@bp.route('/books/new')
@rights_required('admin')
def new():
    return render_template('books/new.html', book=Book(),
                           genres=all_genres(), selected_genre_ids=[])


@bp.route('/books', methods=['POST'])
@rights_required('admin')
def create():
    book, selected_genre_ids = book_form_params()
    cover_file = request.files.get('cover')
    saver = None
    try:
        if not (cover_file and cover_file.filename):
            raise ValueError('Не загружена обложка книги.')
        saver = ImageSaver(cover_file)

        book.genres = db.session.execute(
            db.select(Genre).where(Genre.id.in_(selected_genre_ids))
        ).scalars().all() if selected_genre_ids else []

        # Книгу сохраняем до обложки — для обложки нужен идентификатор книги.
        db.session.add(book)
        db.session.flush()
        saver.add_record(book.id)
        db.session.commit()
    except (SQLAlchemyError, ValueError):
        db.session.rollback()
        flash(SAVE_ERROR, 'danger')
        return render_template('books/new.html', book=book,
                               genres=all_genres(),
                               selected_genre_ids=selected_genre_ids)

    # Файл пишем на диск только после успешного коммита.
    saver.store_file()
    flash(f'Книга «{book.title}» успешно добавлена.', 'success')
    return redirect(url_for('books.show', book_id=book.id))


@bp.route('/books/<int:book_id>/edit')
@rights_required('admin', 'moderator')
def edit(book_id):
    book = db.get_or_404(Book, book_id)
    return render_template('books/edit.html', book=book,
                           genres=all_genres(),
                           selected_genre_ids=[g.id for g in book.genres])


@bp.route('/books/<int:book_id>', methods=['POST'])
@rights_required('admin', 'moderator')
def update(book_id):
    book = db.get_or_404(Book, book_id)
    selected_genre_ids = apply_form(book)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(SAVE_ERROR, 'danger')
        return render_template('books/edit.html', book=book,
                               genres=all_genres(),
                               selected_genre_ids=selected_genre_ids)

    flash(f'Книга «{book.title}» успешно обновлена.', 'success')
    return redirect(url_for('books.show', book_id=book.id))


# --- Удаление книги и рецензии реализуются в следующих коммитах ---

@bp.route('/books/<int:book_id>/delete', methods=['POST'])
@rights_required('admin')
def delete(book_id):
    return ('Not implemented', 501)
