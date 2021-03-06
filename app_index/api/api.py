from flask import Blueprint, render_template, send_from_directory, jsonify
from flask import make_response, json, request, current_app as app
from flask import redirect, g
from flask_httpauth import HTTPBasicAuth

from app_index.utils import query_db
from app_index.model import Base, Restaurant, MenuItem, User
from app_index.api import utils

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

api = Blueprint('api', __name__)

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username_or_token, password):
    # check if token
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        user = session.query(User).filter_by(id=user_id).one()
    else:
        user = session.query(User).filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


# API endpoints
@api.route('/images', defaults={'filename': 'filler.jpg'})
@api.route('/images/<filename>')
def image_file(filename):
    return send_from_directory('static/images', filename)


@api.route('/users', methods=['GET', 'POST'])
def users():
    """
    Create or delete users. Takes a json object with values
    email, name, username, picture, and password when creating
    a new user over a POST request.
    """
    if request.method == 'GET':
        users = query_db.get_all(session, User)
        return jsonify(users=[user.serialize for user in users])
    elif request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')

        if username is None or password is None:
            abort(400)
        if session.query(User).filter_by(username=username).first() is not None:
            abort(400)

        user = User(
            username=username,
            name=request.json.get('name', None),
            email=request.json.get('email', None),
            picture=request.json.get('picture', None)
            )
        user.hash_password(password)

        try:
            session.add(user)
            session.commit()

            return jsonify({"username": user.username}), 201
        except:
            session.rollback()
            raise


@api.route('/protected')
@auth.login_required
def protectedAsset():
    return jsonify({"secret key":"love"})


@api.route('/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@api.route('/restaurants/JSON', methods=['GET', 'POST', 'DELETE'])
def restaurantsJSON():
    restaurants = query_db.get_all(session, Restaurant)

    if request.method == 'GET':
        try:
            return json.dumps([restaurant.serialize for restaurant in
                restaurants], ensure_ascii=False)
        except:
            raise
    elif request.method == 'POST':
        restaurant = Restaurant(name=request.args.get('name'))

        if 'user_id' in request.form:
            restaurant.user_id = request.args.get('user_id')
        else:
            restaurant.user_id = 1
        try:
            query_db.update(session, restaurant)
            session.commit()
            return json.dumps([restaurant.serialize for restaurant in
                restaurants], ensure_ascii=False)
        except:
            session.rollback()
            raise
    elif request.method == 'DELETE':
        try:
            restaurant = query_db.get_one(session, Restaurant,
                    request.args.get('id'))
            query_db.delete(session, restaurant)
            session.commit()

            return make_response('succes', 200)
        except:
            session.rollback()
            return make_response('error', 404)

@api.route('/newRestaurant/JSON', methods=['POST'])
def newRestaurant():
    address = request.args.get('address', '')
    meal_type = request.args.get('meal_type', '')
    restaurant_info = utils.findRestaurant(address, meal_type)[0]

    if restaurant_info != "No results found":
        restaurant = Restaurant(name=restaurant_info['name'])
        try:
            query_db.update(session, restaurant)
            session.commit()
            restaurants = query_db.get_all(session, Restaurant)
            return json.dumps([restaurant.serialize for restaurant in
                restaurants], ensure_ascii=False)
        except:
            session.rollback()
            raise
            return make_response('Error: ', 404)
    else:
        return make_response('No restaurants found for %s in %s' % (meal_type,
            location), 404)


@api.route('/restaurants/<int:restaurant_id>/JSON')
def restaurantJSON(restaurant_id):
    try:
        restaurant = query_db.get_one(session, Restaurant, restaurant_id)
        return jsonify(restaurant.serialize)
    except:
        raise


@api.route('/restaurants/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    try:
        restaurant = query_db.get_one(session, Restaurant, restaurant_id)
        items = query_db.get_items(session, MenuItem, restaurant_id)
        return jsonify(MenuItems=[item.serialize for item in items])
    except:
        raise


@api.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def restaurantMenuItemJSON(restaurant_id, menu_id):
    try:
        item = query_db.get_one(session, MenuItem, restaurant_id)
        return jsonify(item.serialize)
    except:
        raise


