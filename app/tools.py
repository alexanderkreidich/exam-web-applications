import os
import hashlib

import bleach
import markdown as md
from flask import current_app
from werkzeug.utils import secure_filename

from models import db, Book, Cover, book_genres


def sanitize_markdown(text):
    """Прогоняет пользовательский ввод через санитайзер, экранируя опасные теги."""
    if not text:
        return ''
    return bleach.clean(
        text,
        tags=current_app.config['ALLOWED_TAGS'],
        attributes=current_app.config['ALLOWED_ATTRIBUTES'],
        strip=True,
    )


def render_markdown(text):
    """Преобразует Markdown в HTML для отображения."""
    if not text:
        return ''
    return md.markdown(text, extensions=['extra', 'nl2br'])


class ImageSaver:
    """Сохранение обложки книги: вычисление MD5, запись БД-записи и файла.

    Файл записывается на диск только после успешного коммита транзакции,
    поэтому при ошибке БД не приходится удалять файл. Идентичные изображения
    (с одинаковым MD5) хранятся в одном файле — повторно файл не пишется.
    """

    def __init__(self, file):
        self.file = file
        self.bytes = file.read()
        self.md5_hash = hashlib.md5(self.bytes).hexdigest()
        _, self.ext = os.path.splitext(secure_filename(file.filename) or '')

    def add_record(self, book_id):
        cover = Cover(
            file_name=secure_filename(self.file.filename) or 'cover',
            mime_type=self.file.mimetype or 'application/octet-stream',
            md5_hash=self.md5_hash,
            book_id=book_id,
        )
        db.session.add(cover)
        return cover

    def store_file(self):
        folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, self.md5_hash + self.ext)
        if not os.path.exists(path):
            with open(path, 'wb') as out:
                out.write(self.bytes)


class BooksFilter:
    """Поиск книг по форме на главной странице (индивидуальный вариант 3)."""

    def __init__(self, title=None, author=None, genre_ids=None,
                 years=None, pages_from=None, pages_to=None):
        self.title = title
        self.author = author
        self.genre_ids = genre_ids or []
        self.years = years or []
        self.pages_from = pages_from
        self.pages_to = pages_to

    def perform(self):
        query = db.select(Book)

        if self.title:
            query = query.where(Book.title.ilike(f'%{self.title}%'))
        if self.author:
            query = query.where(Book.author.ilike(f'%{self.author}%'))
        if self.years:
            query = query.where(Book.year.in_(self.years))
        if self.pages_from:
            query = query.where(Book.pages >= self.pages_from)
        if self.pages_to:
            query = query.where(Book.pages <= self.pages_to)
        if self.genre_ids:
            query = query.where(
                Book.id.in_(
                    db.select(book_genres.c.book_id)
                    .where(book_genres.c.genre_id.in_(self.genre_ids))
                )
            )

        return query.order_by(Book.year.desc(), Book.id.desc())
