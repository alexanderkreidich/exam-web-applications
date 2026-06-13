from flask import (
    Blueprint, render_template, request, flash, redirect, url_for,
)
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from models import db, Book, Review
from tools import sanitize_markdown

bp = Blueprint('reviews', __name__)

# Варианты оценки: на сервер передаётся число, пользователю показывается название.
RATINGS = [
    (5, 'отлично'),
    (4, 'хорошо'),
    (3, 'удовлетворительно'),
    (2, 'неудовлетворительно'),
    (1, 'плохо'),
    (0, 'ужасно'),
]


def user_review_for(book_id):
    """Рецензия текущего пользователя на книгу, если она есть."""
    if not current_user.is_authenticated:
        return None
    return db.session.execute(
        db.select(Review).where(
            Review.book_id == book_id, Review.user_id == current_user.id)
    ).scalar()


@bp.route('/books/<int:book_id>/reviews/new')
@login_required
def new(book_id):
    book = db.get_or_404(Book, book_id)
    # Если рецензия уже есть — повторно писать нельзя.
    if user_review_for(book_id):
        return redirect(url_for('books.show', book_id=book_id))
    return render_template('reviews/new.html', book=book, ratings=RATINGS)


@bp.route('/books/<int:book_id>/reviews', methods=['POST'])
@login_required
def create(book_id):
    book = db.get_or_404(Book, book_id)
    if user_review_for(book_id):
        return redirect(url_for('books.show', book_id=book_id))

    try:
        review = Review(
            book_id=book.id,
            user_id=current_user.id,
            rating=request.form.get('rating', type=int),
            text=sanitize_markdown(request.form.get('text')),
        )
        db.session.add(review)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash('При сохранении рецензии возникла ошибка. '
              'Проверьте корректность введённых данных.', 'danger')
        return render_template('reviews/new.html', book=book, ratings=RATINGS)

    flash('Рецензия успешно сохранена.', 'success')
    return redirect(url_for('books.show', book_id=book.id))
