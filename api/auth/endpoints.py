"""Routes for module books"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, decode_token
from flask_bcrypt import Bcrypt
import base64

from helper.db_helper import get_connection

bcrypt = Bcrypt()
auth_endpoints = Blueprint('auth', __name__)

@auth_endpoints.route('/login', methods=['POST'])
def login():
    """Routes for authentication"""
    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM users WHERE username = %s"
    request_query = (username,)
    cursor.execute(query, request_query)
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if not user or not bcrypt.check_password_hash(user.get('password'), password):
        return jsonify({"msg": "Bad username or password"}), 401

    user_id = user.get('user_id')  # Assuming the user_id field is present in the user record
    access_token = create_access_token(
        identity={'user_id': user_id, 'username': username}, additional_claims={'roles': user.get('roles')}
    )
    decoded_token = decode_token(access_token)
    expires = decoded_token['exp']
    return jsonify({
        "access_token": access_token,
        "expires_in": expires,
        "token_type": "Bearer"
    })

@auth_endpoints.route('/register', methods=['POST'])
def register():
    """Routes for register"""
    username = request.form['username']
    email = request.form['email']
    full_name = request.form['full_name']
    phone = request.form['phone']
    password = request.form['password']

    # Check if username already exists
    connection = get_connection()
    cursor = connection.cursor()
    username_check_query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(username_check_query, (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        return jsonify({"message": "Failed", "description": "Username already exists"}), 400

    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Insert new user into database
    insert_query = "INSERT INTO users (username, email, full_name, phone, password) VALUES (%s, %s, %s, %s, %s)"
    request_insert = (username, email, full_name, phone, hashed_password)
    cursor.execute(insert_query, request_insert)
    connection.commit()
    new_id = cursor.lastrowid
    cursor.close()

    if new_id:
        return jsonify({"message": "OK", "description": "User created", "username": username}), 201
    else:
        return jsonify({"message": "Failed", "description": "Failed to register user"}), 500
