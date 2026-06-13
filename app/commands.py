import click
from flask.cli import with_appcontext

from models import db, Role, Genre, User

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


def init_commands(app):
    app.cli.add_command(seed)
