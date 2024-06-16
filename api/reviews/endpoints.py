"""Routes for module books"""
import os
from flask import Blueprint, jsonify, request
from helper.db_helper import get_connection
from helper.form_validation import get_form_data
import uuid

reviews_endpoints = Blueprint('reviews', __name__)
UPLOAD_FOLDER = "img"

@reviews_endpoints.route('/add_review/<int:user_id>/<int:instrument_id>', methods=['POST'])
def add_review(user_id, instrument_id):
    """Route to add a review to the reviews table."""
    # Collect form data
    rating = request.form.get('rating')
    comment = request.form.get('comment')  # Comment is optional

    # Check if the rating is provided
    if not rating:
        return jsonify({"message": "Rating is required."}), 400

    # Ensure rating is an integer and within the range 0-5
    try:
        rating = int(rating)
        if rating < 0 or rating > 5:
            return jsonify({"message": "Rating must be an integer between 0 and 5."}), 400
    except ValueError:
        return jsonify({"message": "Rating must be an integer."}), 400

    # Check if the user has already reviewed this instrument
    connection = get_connection()
    cursor = connection.cursor()
    
    check_query = """
        SELECT COUNT(*) FROM reviews WHERE instrument_id = %s AND user_id = %s
    """
    cursor.execute(check_query, (instrument_id, user_id))
    review_exists = cursor.fetchone()[0] > 0

    if review_exists:
        cursor.close()
        return jsonify({"message": "User has already reviewed this instrument."}), 400

    # Insert the new review into the reviews table
    insert_query = """
        INSERT INTO reviews (instrument_id, user_id, rating, comment)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(insert_query, (instrument_id, user_id, rating, comment))
    connection.commit()
    rows_affected = cursor.rowcount  # Get the number of rows affected by the insert
    cursor.close()

    if rows_affected > 0:
        return jsonify({"message": "Review added successfully."}), 201
    else:
        return jsonify({"message": "Failed to add review."}), 500

@reviews_endpoints.route('/delete_review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """Route to delete a review from the reviews table."""
    connection = get_connection()
    cursor = connection.cursor()
    
    delete_query = "DELETE FROM reviews WHERE review_id = %s"
    cursor.execute(delete_query, (review_id,))
    connection.commit()
    rows_affected = cursor.rowcount  # Get the number of rows affected by the delete
    cursor.close()

    if rows_affected > 0:
        return jsonify({"message": "Review deleted successfully."}), 200
    else:
        return jsonify({"message": "Failed to delete review."}), 500