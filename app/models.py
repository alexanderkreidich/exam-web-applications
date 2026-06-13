import os
from typing import Optional, List
from datetime import datetime

import sqlalchemy as sa
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    String, Text, Integer, ForeignKey, MetaData, Table, Column,
)


class Base(DeclarativeBase):
    # Соглашение об именовании ограничений — нужно для корректных миграций под MySQL.
    metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    })


db = SQLAlchemy(model_class=Base)


# Соединительная таблица «многие ко многим» между книгами и жанрами.
book_genres = Table(
    'book_genres',
    Base.metadata,
    Column('book_id', ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True),
)


class Role(Base):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text)

    def __repr__(self):
        return '<Role %r>' % self.name


class User(Base, UserMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    last_name: Mapped[str] = mapped_column(String(100))
    first_name: Mapped[str] = mapped_column(String(100))
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'))

    role: Mapped['Role'] = relationship(lazy=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return ' '.join(filter(None, [self.last_name, self.first_name, self.middle_name]))

    @property
    def is_admin(self):
        return self.role is not None and self.role.name == 'admin'

    @property
    def is_moderator(self):
        return self.role is not None and self.role.name == 'moderator'

    @property
    def can_edit_books(self):
        return self.is_admin or self.is_moderator

    @property
    def can_delete_books(self):
        return self.is_admin

    def __repr__(self):
        return '<User %r>' % self.login


class Genre(Base):
    __tablename__ = 'genres'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    def __repr__(self):
        return '<Genre %r>' % self.name


class Book(Base):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    short_desc: Mapped[str] = mapped_column(Text)
    year: Mapped[int] = mapped_column(Integer)
    publisher: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(255))
    pages: Mapped[int] = mapped_column(Integer)

    genres: Mapped[List['Genre']] = relationship(secondary=book_genres, lazy='selectin')
    cover: Mapped[Optional['Cover']] = relationship(
        back_populates='book', cascade='all, delete-orphan', uselist=False)
    reviews: Mapped[List['Review']] = relationship(
        back_populates='book', cascade='all, delete-orphan')

    @property
    def reviews_count(self):
        return db.session.scalar(
            sa.select(sa.func.count(Review.id)).where(Review.book_id == self.id))

    @property
    def rating(self):
        avg = db.session.scalar(
            sa.select(sa.func.avg(Review.rating)).where(Review.book_id == self.id))
        return round(avg, 1) if avg is not None else 0

    def __repr__(self):
        return '<Book %r>' % self.title


class Cover(Base):
    __tablename__ = 'covers'

    id: Mapped[int] = mapped_column(primary_key=True)
    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    md5_hash: Mapped[str] = mapped_column(String(32), unique=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey('books.id', ondelete='CASCADE'))

    book: Mapped['Book'] = relationship(back_populates='cover')

    @property
    def storage_filename(self):
        _, ext = os.path.splitext(self.file_name)
        return str(self.id) + ext

    @property
    def url(self):
        return url_for('cover', cover_id=self.id)

    def __repr__(self):
        return '<Cover %r>' % self.file_name


class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey('books.id', ondelete='CASCADE'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    rating: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    book: Mapped['Book'] = relationship(back_populates='reviews')
    user: Mapped['User'] = relationship()

    def __repr__(self):
        return '<Review %r>' % self.id
