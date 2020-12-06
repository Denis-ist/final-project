# -*- coding: utf-8 -*-
import os
from app import app, db, csrf
from flask import render_template, redirect, url_for, request, send_from_directory, g
from flask_paginate import Pagination
from app.models import User, Post, Category, Comments
from app.forms import RegistrationForm, LoginForm, PostForm, SearchForm, CommentForm
from datetime import datetime, timedelta
from app import login
from flask_login import login_user, logout_user, current_user, login_required
from bs4 import BeautifulSoup
from flask_babel import get_locale, lazy_gettext as _l
from flask_ckeditor import upload_success, upload_fail
import uuid


@app.route('/files/<path:filename>')
def uploaded_files(filename):
    path = '/uploaded/'
    return send_from_directory(path, filename)


@app.route('/upload', methods=['POST'])
@csrf.exempt
def upload():
    f = request.files.get('upload')
    extension = f.filename.split('.')[-1].lower()
    if extension not in ['jpg', 'gif', 'png', 'jpeg']:
        return upload_fail(message='Image only!')
    unique_filename = str(uuid.uuid4())
    f.filename = unique_filename + '.' + extension
    f.save(os.path.join('/uploaded/', f.filename))
    url = url_for('uploaded_files', filename=f.filename)
    return upload_success(url=url)  # return upload_success call


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.search_form = SearchForm()
    g.locale = str(get_locale())


@login.user_loader
def load_user(ids):
    return User.query.get(int(ids))


@app.errorhandler(401)
def redirect_for_unauthenticated(error):
    return redirect(url_for("login"))


@app.route('/search')
def search():
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, 6)
    next_url = url_for('search', q=g.search_form.q.data, page=page + 1) \
        if total > page * 10 else None
    prev_url = url_for('search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_l('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('view_personal', id_user=current_user.id))
    return render_template('index.html', title='Добро пожаловать!')


@app.route('/posts')
def post_all():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.id.desc()).paginate(page, 10)
    pagination = Pagination(page=page, total=len(Post.query.all()), css_framework='bootstrap4',
                            per_page=10, )
    return render_template('posts.html', posts=posts, pagination=pagination, show_category=True, title='Все публикации')


@app.route('/posts/<int:id_post>')
def view_post(id_post):
    post = Post.query.get(id_post)
    users = User.query.filter(User.id == Comments.author_id).all()
    form = CommentForm()
    if post.view_counter is None:
        post.view_counter = 0
    post.view_counter += 1
    db.session.commit()
    comments = Comments.query.filter(Comments.post_id == post.id).order_by(Comments.id.desc())  # post.comment
    return render_template('view_post.html', post=post, comments=comments, form=form, users=users, title='Просмотр')


@app.route('/user/<int:id_user>')
@login_required
def view_personal(id_user):
    posts = Post.query.filter(Post.author_id == current_user.id).order_by(Post.id.desc())
    user = User.query.get(id_user)
    return render_template('personal.html', posts=posts, user=user, show_category=True, title='Личная страница')


@app.route('/posts/<int:id_post>', methods=['GET', 'POST'])
@login_required
def create_comment(id_post):
    form = CommentForm()
    if form.validate_on_submit():
        user = User.query.filter(User.email == current_user.email).one()
        post = Post.query.get(id_post)
        new_comment = Comments(
            text=form.text.data,
            date_created=datetime.now() - timedelta(hours=3),
            author_id=user.id,
            post_id=post.id
        )
        db.session.add(new_comment)
        if post.comment_counter is None:
            post.comment_counter = 0
        post.comment_counter += 1
        db.session.commit()
        return redirect(url_for('view_post', id_post=post.id))
    return form


@app.route('/category/<string:name>')
def view_category(name):
    category = Category.query.filter_by(name=name).one()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter(Post.category == category).order_by(Post.id.desc()).paginate(page, 9)
    pagination = Pagination(page=page, total=Post.query.filter(Post.category == category).count(),
                            css_framework='bootstrap4',
                            per_page=9, )
    return render_template('posts.html', posts=posts, pagination=pagination, category=category, show_category=False,
                           title='Категории')


@app.route('/new', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        user = User.query.filter(User.email == current_user.email).one()
        preview_text, word_count, is_sliced = '', 0, False
        text = form.text.data
        words = BeautifulSoup(text, 'html.parser').text.split()
        for word in words:
            preview_text += word + ' '
            word_count += 1
            if word_count == app.config['INTRO_WORDS_COUNT']:
                break
        if word_count < len(words):
            intro_text = preview_text.rstrip() + '...'
        else:
            intro_text = preview_text.rstrip()
        new_post = Post(
            heading=form.heading.data,
            text=text,
            intro_text=intro_text,
            date_created=datetime.now() - timedelta(hours=3),
            author_id=user.id,
            category_id=form.category.data,
            view_counter=0
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('post_all'))
    return render_template('create_post.html', form=form, title='Новая запись')


@app.route('/posts/<int:id_post>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(id_post):
    post = Post.query.get(id_post)
    if current_user.id == post.author_id:
        form = PostForm(
            heading=post.heading,
            text=post.text,
            category=post.category_id
        )
        if form.validate_on_submit():
            preview_text, word_count, is_sliced = '', 0, False
            text = form.text.data
            words = BeautifulSoup(text, 'html.parser').text.split()
            for word in words:
                preview_text += word + ' '
                word_count += 1
                if word_count == app.config['INTRO_WORDS_COUNT']:
                    break
            if word_count < len(words):
                intro_text = preview_text.rstrip() + '...'
            else:
                intro_text = preview_text.rstrip()
            post.heading = form.heading.data
            post.text = form.text.data
            post.category_id = form.category.data
            post.intro_text = intro_text
            db.session.commit()
            return redirect(url_for('view_post', id_post=id_post))
        return render_template('create_post.html', form=form)
    return redirect(url_for('view_post', id_post=id_post, title='Редактирование'))


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = RegistrationForm()
    if form.validate_on_submit():
        register_data = {
            'name': form.name.data,
            'email': form.email.data,
            'password': form.password.data,
        }
        if User.query.filter(User.email == register_data['email']).one_or_none() is not None:
            return render_template('registration.html', form=form, error="Такой пользователь уже существует!")
        new_user = User(email=register_data['email'], name=register_data['name'])
        new_user.set_password(register_data['password'])
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('registration.html', form=form, title='Регистрация')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        login_data = {
            'email': form.email.data,
            'password': form.password.data,
            'remember_me': form.remember_me.data
        }
        user_db = User.query.filter(User.email == login_data['email']).one_or_none()
        if user_db is not None and user_db.check_password(login_data['password']):
            login_user(user_db)
            app.logger.info(f'Пользователь [{user_db.name}] успешно вошел на сайт')
            return redirect(url_for('index'))
        error = "Неправильный логин или пароль!"
        app.logger.error(error)
    return render_template('login.html', title='Войти на сайт', form=form, error=error)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
