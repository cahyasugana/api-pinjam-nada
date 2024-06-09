"""Routes for module books"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, decode_token
from flask_bcrypt import Bcrypt

from helper.db_helper import get_connection

bcrypt = Bcrypt()
auth_endpoints = Blueprint('auth', __name__)


@auth_endpoints.route('/login', methods=['POST'])
def login():
    """Routes for authentication"""
    username = request.json['username']
    password = request.json['kata_sandi']

    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM pengguna WHERE username = %s"
    request_query = (username,)
    cursor.execute(query, request_query) 
    user = cursor.fetchone()
    cursor.close()

    idUser = user.get('id_pengguna')

    if not user or not bcrypt.check_password_hash(user.get('kata_sandi'), password):
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(
        identity={'username': username}, additional_claims={'roles': user['role']})
    decoded_token = decode_token(access_token)
    expires = decoded_token['exp']
    return jsonify({"access_token": access_token, "expires_in": expires, "type": "Bearer", "id_pengguna": idUser})


@auth_endpoints.route('/register', methods=['POST'])
def register():
    """Routes for register"""
    username = request.form['username']
    password = request.form['kata_sandi']
    # To hash a password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    connection = get_connection()
    cursor = connection.cursor()
    insert_query = "INSERT INTO pengguna (username, kata_sandi) values (%s, %s)"
    request_insert = (username, hashed_password)
    cursor.execute(insert_query, request_insert)
    connection.commit()
    cursor.close()
    new_id = cursor.lastrowid
    if new_id:
        return jsonify({"message": "OK",
                        "description": "User created",
                        "username": username}), 201
    return jsonify({"message": "Failed, cant register user"}), 501
