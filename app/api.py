from flask import Blueprint, jsonify, request
from app.models import Post, Category

api = Blueprint('api_module', __name__)


@api.route('/posts')
def posts_api():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.id.desc()).paginate(page, 5)
    return jsonify([post.to_dict() for post in posts.items])


@api.route('/category')
def category_api():
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories])