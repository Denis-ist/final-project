# -*- coding: utf-8 -*-
from app.models import User, Post, Category
from app import app, db
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from flask_login import current_user

from flask import redirect, url_for


class ModelViewSecured(ModelView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.email == app.config['ADMIN_EMAIL']
        return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


admin = Admin(app, name='blog-admin', template_mode='bootstrap3')
admin.add_view(ModelViewSecured(User, db.session))
admin.add_view(ModelViewSecured(Post, db.session))
admin.add_view(ModelViewSecured(Category, db.session))
