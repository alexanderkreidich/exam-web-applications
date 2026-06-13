from functools import wraps

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, abort,
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user,
)

from models import db, User

bp = Blueprint('auth', __name__, url_prefix='/auth')


def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = (
        'Для выполнения данного действия необходимо пройти процедуру аутентификации.')
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)
    login_manager.init_app(app)


def load_user(user_id):
    return db.session.execute(
        db.select(User).filter_by(id=user_id)).scalar()


def rights_required(*roles):
    """Доступ только пользователям с одной из указанных ролей."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role is None or current_user.role.name not in roles:
                flash('У вас недостаточно прав для выполнения данного действия.', 'warning')
                return redirect(url_for('books.index'))
            return view(*args, **kwargs)
        return wrapper
    return decorator


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        remember = request.form.get('remember_me') == 'on'
        if login and password:
            user = db.session.execute(
                db.select(User).filter_by(login=login)).scalar()
            if user and user.check_password(password):
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('books.index'))
        flash('Невозможно аутентифицироваться с указанными логином и паролем.', 'danger')
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(request.referrer or url_for('books.index'))
