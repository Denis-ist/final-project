# -*- coding: utf-8 -*-
from app import db
from app.search import add_to_index, remove_from_index, query_index
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))

        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True)
    name = db.Column(db.String, unique=True)
    password_hash = db.Column(db.String())
    posts = db.relationship('Post', backref='author', lazy="dynamic")  # Post.author
    comments = db.relationship('Comments', backref='comment', lazy="dynamic")  # Comments.comment

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String, unique=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    post = db.relationship('Post', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'alias': self.alias,
            'name': self.name
        }


class Post(SearchableMixin, db.Model):
    __searchable__ = ['text', 'heading']
    id = db.Column(db.Integer, primary_key=True)
    heading = db.Column(db.String(120))
    intro_text = db.Column(db.String)
    text = db.Column(db.String)
    date_created = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    view_counter = db.Column(db.Integer, default=0)
    comment_counter = db.Column(db.Integer, default=0)
    category = db.relationship('Category')
    comment = db.relationship('Comments')

    def to_dict(self):
        return {
            'userId': self.author_id,
            'id': self.id,
            'title': self.heading,
            'body': self.intro_text
        }

    def __repr__(self):
        return f'<Post "{self.heading}">'


class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    date_created = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def to_dict(self):
        return {
            'author_id': self.author_id,
        }
