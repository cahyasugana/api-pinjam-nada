"""Routes for module books"""
import os
from flask import Blueprint, jsonify, request
from helper.db_helper import get_connection
from helper.form_validation import get_form_data
from datetime import datetime
import uuid

loan_endpoints = Blueprint('loan', __name__)
UPLOAD_FOLDER = "img"

@loan_endpoints.route('/request_loan/<int:requester_id>', methods=['POST'])
def request_loan(requester_id):
    """Route to request a loan for an instrument."""
    # Collect form data
    instrument_id = request.form.get('instrument_id')
    message = request.form.get('message')

    # Check if all required fields are provided
    if not all([instrument_id, message]):
        return jsonify({"message": "All fields are required."}), 400

    # Get the current date and time
    request_date = datetime.now()

    # Get the instrument owner_id to ensure requester is not the owner
    connection = get_connection()
    cursor = connection.cursor()

    select_query = "SELECT owner_id FROM instruments WHERE instrument_id = %s"
    cursor.execute(select_query, (instrument_id,))
    instrument = cursor.fetchone()

    if not instrument:
        cursor.close()
        return jsonify({"message": "Instrument not found."}), 404

    owner_id = instrument[0]

    if requester_id == owner_id:
        cursor.close()
        return jsonify({"message": "You cannot loan your own instrument."}), 400

    # Check if the requester has already requested this instrument
    duplicate_check_query = """
        SELECT COUNT(*) FROM loanrequests
        WHERE instrument_id = %s AND requester_id = %s
    """
    cursor.execute(duplicate_check_query, (instrument_id, requester_id))
    duplicate_count = cursor.fetchone()[0]

    if duplicate_count > 0:
        cursor.close()
        return jsonify({"message": "You have already requested this instrument."}), 400

    # Insert the new loan request into the loanrequests table
    insert_query = """
        INSERT INTO loanrequests (instrument_id, requester_id, request_date, message)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(insert_query, (instrument_id, requester_id, request_date, message))
    connection.commit()
    rows_affected = cursor.rowcount  # Get the number of rows affected by the insert
    cursor.close()

    if rows_affected > 0:
        return jsonify({"requester_id": requester_id, "message": "Loan request submitted successfully."}), 201
    else:
        return jsonify({"message": "Failed to submit loan request."}), 500

@loan_endpoints.route('/cancel_loan_request/<int:requester_id>/<int:request_id>', methods=['DELETE'])
def cancel_loan_request(requester_id, request_id):
    """Route to cancel a loan request."""
    # Connect to the database
    connection = get_connection()
    cursor = connection.cursor()

    # Check if the loan request exists and belongs to the requester
    select_query = """
        SELECT * FROM loanrequests
        WHERE request_id = %s AND requester_id = %s
    """
    cursor.execute(select_query, (request_id, requester_id))
    loan_request = cursor.fetchone()

    if not loan_request:
        cursor.close()
        return jsonify({"message": "Loan request not found or you do not have permission to cancel this request."}), 404

    # Delete the loan request
    delete_query = "DELETE FROM loanrequests WHERE request_id = %s"
    cursor.execute(delete_query, (request_id,))
    connection.commit()
    rows_affected = cursor.rowcount  # Get the number of rows affected by the delete operation
    cursor.close()

    if rows_affected > 0:
        return jsonify({"message": "Loan request cancelled successfully."}), 200
    else:
        return jsonify({"message": "Failed to cancel loan request."}), 500

@loan_endpoints.route('/loan_requests/<int:requester_id>', methods=['GET'])
def get_loan_requests(requester_id):
    """Route to get all instruments requested by a specific user."""
    # Connect to the database
    connection = get_connection()
    cursor = connection.cursor()

    # Query to get all instruments requested by the requester
    select_query = """
        SELECT i.instrument_id, i.owner_id, i.instrument_name, i.description, i.location, i.availability_status, i.image, i.instrument_type_id
        FROM loanrequests lr
        JOIN instruments i ON lr.instrument_id = i.instrument_id
        WHERE lr.requester_id = %s
    """
    cursor.execute(select_query, (requester_id,))
    instruments = cursor.fetchall()

    cursor.close()
    connection.close()

    if not instruments:
        return jsonify({"message": "No loan requests found for this user."}), 404

    # Prepare the list of instruments to return
    instruments_list = []
    for instrument in instruments:
        instrument_data = {
            "instrument_id": instrument[0],
            "owner_id": instrument[1],
            "instrument_name": instrument[2],
            "description": instrument[3],
            "location": instrument[4],
            "availability_status": instrument[5],
            "image": instrument[6],
            "instrument_type_id": instrument[7]
        }
        instruments_list.append(instrument_data)

    return jsonify({"requester_id": requester_id, "instruments": instruments_list}), 200