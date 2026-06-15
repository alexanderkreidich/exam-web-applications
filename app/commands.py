import os
import hashlib

import click
from flask import current_app
from flask.cli import with_appcontext

from models import db, Role, Genre, User, Book, Cover, Review
from demo_data import BOOKS as DEMO_BOOKS, REVIEWS as DEMO_REVIEWS

ROLES = [
    ('admin', 'Суперпользователь, имеет полный доступ к системе, '
              'в том числе к созданию и удалению книг.'),
    ('moderator', 'Может редактировать данные книг и производить '
                  'модерацию рецензий.'),
    ('user', 'Может оставлять рецензии.'),
]

GENRES = [
    'Роман', 'Фантастика', 'Детектив', 'Поэзия', 'Научная литература',
    'Фэнтези', 'Историческая проза', 'Приключения',
]


@click.command('seed')
@with_appcontext
def seed():
    """Заполняет справочники (роли, жанры) и создаёт учётную запись администратора.

    Жанры, роли и пользователи задаются напрямую в СУБД, отдельная админка
    для них не предусмотрена.
    """
    for name, description in ROLES:
        if not db.session.scalar(db.select(Role).filter_by(name=name)):
            db.session.add(Role(name=name, description=description))

    for name in GENRES:
        if not db.session.scalar(db.select(Genre).filter_by(name=name)):
            db.session.add(Genre(name=name))

    db.session.commit()

    if not db.session.scalar(db.select(User).filter_by(login='admin')):
        admin_role = db.session.scalar(db.select(Role).filter_by(name='admin'))
        admin = User(login='admin', last_name='Крейдич', first_name='Александр',
                     middle_name='Дмитриевич', role_id=admin_role.id)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        click.echo('Создан администратор: логин "admin", пароль "admin".')

    click.echo('Справочники заполнены.')


@click.command('demo')
@with_appcontext
def demo():
    """Загружает демонстрационный набор книг с обложками и рецензиями.

    Обложки берутся из заранее подготовленных файлов seed_assets/covers/.
    Команда идемпотентна: уже существующие книги пропускаются.
    """
    assets = os.path.join(os.path.dirname(__file__), 'seed_assets', 'covers')
    upload = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload, exist_ok=True)

    genres = {g.name: g for g in db.session.execute(db.select(Genre)).scalars()}
    created = 0
    for data in DEMO_BOOKS:
        if db.session.scalar(db.select(Book).filter_by(title=data['title'])):
            continue
        book = Book(title=data['title'], short_desc=data['desc'], year=data['year'],
                    publisher=data['publisher'], author=data['author'], pages=data['pages'])
        book.genres = [genres[g] for g in data['genres'] if g in genres]
        db.session.add(book)
        db.session.flush()

        with open(os.path.join(assets, data['slug'] + '.png'), 'rb') as f:
            png = f.read()
        md5 = hashlib.md5(png).hexdigest()
        db.session.add(Cover(file_name=data['slug'] + '.png', mime_type='image/png',
                             md5_hash=md5, book_id=book.id))
        path = os.path.join(upload, md5 + '.png')
        if not os.path.exists(path):
            with open(path, 'wb') as out:
                out.write(png)
        created += 1
    db.session.commit()

    # Демонстрационные учётные записи модератора и пользователя.
    demo_users = [('moderator', 'moderator', 'Петров', 'Пётр'),
                  ('reader', 'user', 'Иванов', 'Иван')]
    for login, role_name, last, first in demo_users:
        if not db.session.scalar(db.select(User).filter_by(login=login)):
            role = db.session.scalar(db.select(Role).filter_by(name=role_name))
            u = User(login=login, last_name=last, first_name=first, role_id=role.id)
            u.set_password(login)
            db.session.add(u)
    db.session.commit()

    users = {u.login: u for u in db.session.execute(db.select(User)).scalars()}
    rev_count = 0
    for slug, items in DEMO_REVIEWS.items():
        meta = next((b for b in DEMO_BOOKS if b['slug'] == slug), None)
        book = db.session.scalar(db.select(Book).filter_by(title=meta['title'])) if meta else None
        if not book:
            continue
        for login, rating, text in items:
            user = users.get(login)
            if not user or db.session.scalar(
                    db.select(Review).filter_by(book_id=book.id, user_id=user.id)):
                continue
            db.session.add(Review(book_id=book.id, user_id=user.id, rating=rating, text=text))
            rev_count += 1
    db.session.commit()

    click.echo(f'Демо-данные загружены: книг добавлено {created}, рецензий {rev_count}.')


def init_commands(app):
    app.cli.add_command(seed)
    app.cli.add_command(demo)
