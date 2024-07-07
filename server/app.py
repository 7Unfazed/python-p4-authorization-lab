#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, Article, User

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json_encoder.compact = False

migrate = Migrate(app, db)
db.init_app(app)

api = Api(app)

class ClearSession(Resource):
    def delete(self):
        session.clear()
        return {}, 204

class IndexArticle(Resource):
    def get(self):
        articles = [article.to_dict() for article in Article.query.all()]
        return make_response(jsonify(articles), 200)

class ShowArticle(Resource):
    def get(self, id):
        article = Article.query.filter(Article.id == id).first()
        if not article:
            return {'error': 'Article not found'}, 404
        
        article_json = article.to_dict()

        if not session.get('user_id'):
            session['page_views'] = session.get('page_views', 0) + 1
            if session['page_views'] > 3:
                return {'message': 'Maximum pageview limit reached'}, 401

        return article_json, 200

class Login(Resource):
    def post(self):
        username = request.get_json().get('username')
        user = User.query.filter(User.username == username).first()
        if user:
            session['user_id'] = user.id
            return user.to_dict(), 200
        return {'error': 'Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        session.clear()
        return {}, 204

class CheckSession(Resource):
    def get(self):
        if 'user_id' in session:
            user_id = session['user_id']
            user = User.query.filter(User.id == user_id).first()
            if user:
                return user.to_dict(), 200
        return {'error': 'Unauthorized'}, 401

class MemberOnlyIndex(Resource):
    def get(self):
        if 'user_id' not in session:
            return {'error': 'Unauthorized access'}, 401
        
        articles = [article.to_dict() for article in Article.query.filter_by(is_member_only=True).all()]
        return jsonify(articles), 200

class MemberOnlyArticle(Resource):
    def get(self, id):
        if 'user_id' not in session:
            return {'error': 'Unauthorized access'}, 401
        
        article = Article.query.filter_by(id=id, is_member_only=True).first()
        if not article:
            return {'error': 'Article not found or not member-only'}, 404
        
        return article.to_dict(), 200

api.add_resource(ClearSession, '/clear')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')
api.add_resource(MemberOnlyIndex, '/members_only_articles')
api.add_resource(MemberOnlyArticle, '/members_only_articles/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
