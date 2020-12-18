# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms.fields import StringField, PasswordField, SelectField, TextAreaField, SubmitField, \
    BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Email, DataRequired, EqualTo, Length
from flask_ckeditor import CKEditorField
from flask import request
from flask_babel import lazy_gettext as _l
from app.models import Category


class RegistrationForm(FlaskForm):
    name = StringField('Имя пользователя:', validators=[DataRequired()])
    email = EmailField('Ваш email:', validators=[DataRequired(), Email()])
    password = PasswordField('Ваш пароль:', validators=[DataRequired(),
                                                        EqualTo('repeat_password', message='Пароли не совпадают!'),
                                                        Length(min=6, message='Минимальная длина пароля: 6 символов')])
    repeat_password = PasswordField('Повторите пароль:')
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(message="Вы не ввели email!")])
    password = PasswordField('Пароль', validators=[DataRequired(message="Вы не ввели пароль!"),
                                                   Length(min=6, message="Минимальная длина пароля %(min)d символов!")])
    remember_me = BooleanField('Запомнить меня', default='checked')
    submit = SubmitField('Войти')


class PostForm(FlaskForm):
    heading = StringField('Заголовок статьи', validators=[DataRequired(message="Заголовок обязателен!"),
                                                          Length(min=5, max=50,
                                                                 message="Минимум 5 символов и не более 50")])
    category_list = Category.query.all()
    choices = []
    for category in category_list:
        choices.append((str(category.id), category.alias))
    category = SelectField('Выберите категорию',
                           choices=choices)
    text = CKEditorField('Текст публикации', validators=[DataRequired(message="Поле обязательно для ввода!"),
                                                         Length(min=10, message='Введите больше текста...')])
    submit = SubmitField('Сохранить')


class CommentForm(FlaskForm):
    text = TextAreaField('Комментарий')
    submit = SubmitField('Отправить')


class SearchForm(FlaskForm):
    q = StringField(_l('Что ищем?'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)
