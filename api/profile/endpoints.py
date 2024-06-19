"""Routes for module books"""
import os
from flask import Blueprint, jsonify, request
from helper.db_helper import get_connection
from helper.form_validation import get_form_data
import uuid

profile_endpoints = Blueprint('profile', __name__)
UPLOAD_FOLDER = "img"

@profile_endpoints.route('/read/<int:user_id>', methods=['GET'])
def read_user(user_id):
    """Routes for reading user profile based on user_id"""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Define the select query to fetch user data based on user_id
    select_query = """
        SELECT username, email, full_name, phone, profile_picture 
        FROM users 
        WHERE user_id = %s
    """
    cursor.execute(select_query, (user_id,))
    user = cursor.fetchone()
    
    cursor.close()  # Close the cursor after query execution
    connection.close()  # Close the connection

    if user:
        return jsonify({"message": "OK", "data": user}), 200
    else:
        return jsonify({"message": "Failed", "description": "User not found"}), 404

@profile_endpoints.route('/update/<int:user_id>', methods=['POST'])
def update(user_id):
    """Routes for module to update a user's profile"""
    # Collect optional parameters from the form
    request_data = request.get_json()

    email = request_data.get('email')
    full_name = request_data.get('full_name')
    phone = request_data.get('phone')
    uploaded_file = request.files.get('profile_picture')


    # print(email)
    # print(full_name)
    # print(phone)
    # return jsonify({"message": "OK", "data": email}), 200

    
    # Check if at least one field is provided for update
    if not any([email, full_name, phone, uploaded_file]):
        return jsonify({"message": "No fields provided for update."}), 400

    fields_to_update = []
    values_to_update = []
  
    if email:
        fields_to_update.append("email=%s")
        values_to_update.append(email)
    if full_name:
        fields_to_update.append("full_name=%s")
        values_to_update.append(full_name)
    if phone:
        fields_to_update.append("phone=%s")
        values_to_update.append(phone)

    connection = get_connection()
    cursor = connection.cursor()

    if uploaded_file and uploaded_file.filename != '':
        # Retrieve the current profile picture filename
        cursor.execute("SELECT profile_picture FROM users WHERE user_id=%s", (user_id,))
        current_profile_picture = cursor.fetchone()[0]

        # Generate a unique filename for the new profile picture
        unique_filename = str(uuid.uuid4()) + "_" + uploaded_file.filename
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        uploaded_file.save(file_path)

        fields_to_update.append("profile_picture=%s")
        values_to_update.append(unique_filename)

        # Delete the old profile picture file if it exists
        if current_profile_picture:
            old_file_path = os.path.join(UPLOAD_FOLDER, current_profile_picture)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)

    if fields_to_update:
        update_query = f"UPDATE users SET {', '.join(fields_to_update)} WHERE user_id=%s"
        values_to_update.append(user_id)  # Add user_id to the end of the values list

        cursor.execute(update_query, values_to_update)
        connection.commit()
        rows_affected = cursor.rowcount  # Get the number of rows affected by the update
        cursor.close()

        if rows_affected > 0:
            return jsonify({"user_id": user_id, "message": "Profile updated successfully."}), 200
        else:
            return jsonify({"message": "User not found or profile update failed."}), 404

    cursor.close()
    return jsonify({"message": "No profile picture uploaded."}), 400