"""Routes for module books"""
import os
from flask import Blueprint, jsonify, request
from helper.db_helper import get_connection
from helper.form_validation import get_form_data
import uuid

instruments_endpoints = Blueprint('instruments', __name__)
UPLOAD_FOLDER = "img"

@instruments_endpoints.route('/add_instrument/<int:user_id>', methods=['POST'])
def add_instrument(user_id):
    """Route to add an instrument to the instruments table."""
    # Collect form data
    instrument_name = request.form.get('instrument_name')
    description = request.form.get('description')
    location = request.form.get('location')
    instrument_type_id = request.form.get('instrument_type_id')
    uploaded_file = request.files.get('image')

    # Check if all required fields are provided
    if not all([instrument_name, description, location, instrument_type_id, uploaded_file]):
        return jsonify({"message": "All fields are required."}), 400

    # Save the uploaded image file
    if uploaded_file and uploaded_file.filename != '':
        # Generate a unique filename for the uploaded image
        unique_filename = str(uuid.uuid4())  # Generate a unique hash
        file_extension = os.path.splitext(uploaded_file.filename)[1]  # Get the file extension
        unique_filename += file_extension  # Combine hash and extension
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        uploaded_file.save(file_path)

        # Insert the new instrument into the instruments table
        connection = get_connection()
        cursor = connection.cursor()
        
        insert_query = """
            INSERT INTO instruments (owner_id, instrument_name, description, location, instrument_type_id, image)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (user_id, instrument_name, description, location, instrument_type_id, unique_filename))
        connection.commit()
        rows_affected = cursor.rowcount  # Get the number of rows affected by the insert
        cursor.close()

        if rows_affected > 0:
            return jsonify({"user_id": user_id, "message": "Instrument added successfully."}), 201
        else:
            return jsonify({"message": "Failed to add instrument."}), 500
    else:
        return jsonify({"message": "Image upload failed."}), 400
    
@instruments_endpoints.route('/update_instrument/<int:instrument_id>', methods=['POST'])
def update_instrument(instrument_id):
    """Route to update an instrument in the instruments table."""
    # Collect optional parameters from the form
    instrument_name = request.form.get('instrument_name')
    description = request.form.get('description')
    location = request.form.get('location')
    instrument_type_id = request.form.get('instrument_type_id')
    uploaded_file = request.files.get('image')
    availability_status = request.form.get('availability_status')
    print("tEst")
    # Check if at least one field is provided for update
    if not any([instrument_name, description, location, instrument_type_id, uploaded_file, availability_status]):
        return jsonify({"message": "No fields provided for update."}), 400

    fields_to_update = []
    values_to_update = []

    if instrument_name:
        fields_to_update.append("instrument_name=%s")
        values_to_update.append(instrument_name)
    if description:
        fields_to_update.append("description=%s")
        values_to_update.append(description)
    if location:
        fields_to_update.append("location=%s")
        values_to_update.append(location)
    if instrument_type_id:
        fields_to_update.append("instrument_type_id=%s")
        values_to_update.append(instrument_type_id)
    if availability_status:
        fields_to_update.append("availability_status=%s")
        values_to_update.append(availability_status)

    connection = get_connection()
    cursor = connection.cursor()

    if uploaded_file and uploaded_file.filename != '':
        try:
            # Retrieve the current instrument image filename
            cursor.execute("SELECT image FROM instruments WHERE instrument_id=%s", (instrument_id,))
            current_image = cursor.fetchone()[0]

            # Generate a unique filename for the new image
            unique_filename = str(uuid.uuid4())  # Generate a unique hash
            file_extension = os.path.splitext(uploaded_file.filename)[1].lower()  # Get the file extension
            unique_filename += file_extension  # Combine hash and extension
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            uploaded_file.save(file_path)

            fields_to_update.append("image=%s")
            values_to_update.append(unique_filename)

            # Delete the old image file if it exists
            if current_image:
                old_file_path = os.path.join(UPLOAD_FOLDER, current_image)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

        except Exception as e:
            return jsonify({"message": f"Error uploading image: {str(e)}"}), 500

    if fields_to_update:
        try:
            update_query = f"UPDATE instruments SET {', '.join(fields_to_update)} WHERE instrument_id=%s"
            values_to_update.append(instrument_id)  # Add instrument_id to the end of the values list

            cursor.execute(update_query, values_to_update)
            connection.commit()
            rows_affected = cursor.rowcount  # Get the number of rows affected by the update
            cursor.close()

            if rows_affected > 0:
                return jsonify({"instrument_id": instrument_id, "message": "Instrument updated successfully."}), 200
            else:
                return jsonify({"message": "Instrument not found or update failed."}), 404

        except Exception as e:
            return jsonify({"message": f"Error updating instrument: {str(e)}"}), 500

    cursor.close()
    return jsonify({"message": "No image uploaded."}), 400

@instruments_endpoints.route('/delete_instrument/<int:instrument_id>', methods=['DELETE'])
def delete_instrument(instrument_id):
    """Route to delete an instrument from the instruments table."""
    connection = get_connection()
    cursor = connection.cursor()

    # Retrieve the current instrument image filename
    cursor.execute("SELECT image FROM instruments WHERE instrument_id=%s", (instrument_id,))
    result = cursor.fetchone()
    
    if not result:
        cursor.close()
        return jsonify({"message": "Instrument not found."}), 404

    current_image = result[0]

    # Delete the instrument from the database
    cursor.execute("DELETE FROM instruments WHERE instrument_id=%s", (instrument_id,))
    connection.commit()
    rows_affected = cursor.rowcount  # Get the number of rows affected by the delete
    cursor.close()

    if rows_affected > 0:
        # Delete the image file if it exists
        if current_image:
            image_path = os.path.join(UPLOAD_FOLDER, current_image)
            if os.path.exists(image_path):
                os.remove(image_path)

        return jsonify({"instrument_id": instrument_id, "message": "Instrument deleted successfully."}), 200
    else:
        return jsonify({"message": "Failed to delete instrument."}), 500


@instruments_endpoints.route('/read_instruments_by_user/<int:user_id>', methods=['GET'])
def read_instruments_by_user(user_id):
    """Route to read instruments based on user_id."""
    connection = get_connection()
    cursor = connection.cursor()

    # Query instruments and join with instrument_type based on instrument_type_id and reviews for average rating
    query = """
        SELECT 
                i.instrument_id, 
                i.owner_id, 
                u.username AS owner_username,
                i.instrument_name, 
                i.description, 
                i.location, 
                i.availability_status, 
                i.image, 
                i.instrument_type_id, 
                it.name AS instrument_type,
                COALESCE(AVG(r.rating), 0) AS average_rating
            FROM instruments i
            JOIN users u ON i.owner_id = u.user_id
            JOIN instrument_type it ON i.instrument_type_id = it.id
            LEFT JOIN reviews r ON i.instrument_id = r.instrument_id
            WHERE i.owner_id = %s
            GROUP BY i.instrument_id, i.owner_id, u.username, i.instrument_name, i.description, 
                     i.location, i.availability_status, i.image, i.instrument_type_id, it.name
    """
    cursor.execute(query, (user_id,))
    instruments_data = cursor.fetchall()

    cursor.close()
    connection.close()

    # Stage the data
    staged_data = []
    for instrument in instruments_data:
        staged_data.append({
            "instrument_id": instrument[0],
            "owner_id": instrument[1],
            "owner_username": instrument[2],
            "instrument_name": instrument[3],
            "description": instrument[4],
            "location": instrument[5],
            "availability_status": instrument[6],
            "image": instrument[7],
            "instrument_type_id": instrument[8],
            "instrument_type": instrument[9],
            "average_rating": (instrument[10])  # Ensure average_rating is converted to float
        })

    if staged_data:
        return jsonify({"instruments": staged_data}), 200
    else:
        return jsonify({"message": "No instruments found for the user."}), 404

@instruments_endpoints.route('/read_instruments_by_availability_excluding_user/<int:exclude_user_id>', methods=['GET'])
def read_instruments_by_availability_excluding_user(exclude_user_id):
    """Route to read instruments based on availability status, excluding instruments of a specified user and those already requested by that user."""

    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT 
            i.instrument_id, 
            i.owner_id, 
            u.username AS owner_username,
            i.instrument_name, 
            i.description, 
            i.location, 
            i.availability_status, 
            i.image, 
            i.instrument_type_id, 
            it.name AS instrument_type,
            COALESCE(AVG(r.rating), 0) AS average_rating
        FROM instruments i
        JOIN instrument_type it ON i.instrument_type_id = it.id
        LEFT JOIN reviews r ON i.instrument_id = r.instrument_id
        JOIN users u ON i.owner_id = u.user_id
        LEFT JOIN loanrequests lr ON i.instrument_id = lr.instrument_id AND lr.requester_id = %s
        WHERE i.availability_status IN (1, 2) AND i.owner_id != %s
        AND lr.instrument_id IS NULL
        GROUP BY i.instrument_id, i.owner_id, u.username, i.instrument_name, i.description, 
                 i.location, i.availability_status, i.image, i.instrument_type_id, it.name
    """
    cursor.execute(query, (exclude_user_id, exclude_user_id))

    instruments_data = cursor.fetchall()

    cursor.close()
    connection.close()

    staged_data = []
    for instrument in instruments_data:
        staged_data.append({
            "instrument_id": instrument[0],
            "owner_id": instrument[1],
            "owner_username": instrument[2],
            "instrument_name": instrument[3],
            "description": instrument[4],
            "location": instrument[5],
            "availability_status": instrument[6],
            "image": instrument[7],
            "instrument_type_id": instrument[8],
            "instrument_type": instrument[9],
            "average_rating": instrument[10]
        })

    if staged_data:
        return jsonify({"instruments": staged_data}), 200
    else:
        return jsonify({"message": "No instruments found with the specified availability status."}), 400
