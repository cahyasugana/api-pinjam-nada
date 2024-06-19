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
    

# delete all requested instrument on list
@loan_endpoints.route('/delete_loan_request/<int:instrument_id>', methods=['DELETE'])
def delete_loan_requests(instrument_id):
    """Route to cancel a loan request."""
    # Connect to the database
    connection = get_connection()
    cursor = connection.cursor()

    # Delete the loan request
    delete_query = "DELETE FROM loanrequests WHERE instrument_id = %s"
    cursor.execute(delete_query, (instrument_id,))
    connection.commit()
    rows_affected = cursor.rowcount  # Get the number of rows affected by the delete operation
    cursor.close()

    if rows_affected > 0:
        return jsonify({"message": "Loan request cancelled successfully."}), 200
    else:
        return jsonify({"message": "Failed to cancel loan request."}), 500
    
# delete loan 
@loan_endpoints.route('/delete_loan/<int:instrument_id>', methods=['DELETE'])
def delete_loan(instrument_id):
    """Route to cancel a loan request."""
    # Connect to the database
    connection = get_connection()
    cursor = connection.cursor()

    # Delete the loan request
    delete_query = "DELETE FROM loans WHERE instrument_id = %s"
    cursor.execute(delete_query, (instrument_id,))
    connection.commit()
    rows_affected = cursor.rowcount  # Get the number of rows affected by the delete operation
    cursor.close()

    if rows_affected > 0:
        return jsonify({"message": "Loan request cancelled successfully."}), 200
    else:
        return jsonify({"message": "Failed to cancel loan request."}), 500
    
# add loan
@loan_endpoints.route('/add_loan/<int:instrument_id>', methods=['POST'])
def addloan(instrument_id):
    """Route to request a loan for an instrument."""
    # Collect form data
    borrowed_id = request.form.get('borrowed_id')

    # Check if all required fields are provided
    if not all([instrument_id]):
        return jsonify({"message": "All fields are required."}), 400

    # Get the current date and time
    request_date = datetime.now()

    # Get the instrument owner_id to ensure requester is not the owner
    connection = get_connection()
    cursor = connection.cursor()
    # Insert the new loan request into the loanrequests table
    insert_query = """
        INSERT INTO loans (instrument_id, borrower_id, loan_date)
        VALUES (%s, %s, %s)
    """
    cursor.execute(insert_query, (instrument_id, borrowed_id, request_date))
    connection.commit()
    rows_affected = cursor.rowcount  # Get the number of rows affected by the insert
    cursor.close()

    if rows_affected > 0:
        return jsonify({"message": "Loan request submitted successfully."}), 201
    else:
        return jsonify({"message": "Failed to submit loan request."}), 500
    
# add request loan
@loan_endpoints.route('/add_request_loan/', methods=['POST'])
def addrequestloan():
    """Route to request a loan for an instrument."""
    # Collect form data
    instrumen_id = request.form.get('instrumen_id')
    requester_id = request.form.get('requester_id')
    message= request.form.get('message')
    request_date = datetime.now()

    # Check if all required fields are provided
    if not all([instrumen_id, requester_id, message]):
        return jsonify({"message": "All fields are required."}), 400

    # Get the current date and time
    request_date = datetime.now()

    # Get the instrument owner_id to ensure requester is not the owner
    connection = get_connection()
    cursor = connection.cursor()
    # Insert the new loan request into the loanrequests table
    insert_query = """
        INSERT INTO loanrequests (instrument_id, requester_id, request_date, message)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(insert_query, (instrumen_id, requester_id, request_date, message))
    connection.commit()
    rows_affected = cursor.rowcount  # Get the number of rows affected by the insert
    cursor.close()

    if rows_affected > 0:
        return jsonify({"message": "Loan request submitted successfully."}), 201
    else:
        return jsonify({"message": "Failed to submit loan request."}), 500

@loan_endpoints.route('/cancel_loan_request/<int:requester_id>/<int:instrument_id>', methods=['DELETE'])
def cancel_loan_request(requester_id, instrument_id):
    """Route to cancel all loan requests for a specific instrument by a requester."""
    # Connect to the database
    connection = get_connection()
    cursor = connection.cursor()

    # Check if any loan requests exist and belong to the requester by joining loanrequests and instruments tables
    select_query = """
        SELECT * FROM loanrequests
        JOIN instruments ON loanrequests.instrument_id = instruments.instrument_id
        WHERE loanrequests.requester_id = %s AND loanrequests.instrument_id = %s
    """
    cursor.execute(select_query, (requester_id, instrument_id))
    loan_requests = cursor.fetchall()

    if not loan_requests:
        cursor.close()
        return jsonify({"message": "Loan requests not found or you do not have permission to cancel these requests."}), 404

    # Delete all loan requests for the instrument by the requester
    delete_query = "DELETE FROM loanrequests WHERE instrument_id = %s AND requester_id = %s"
    cursor.execute(delete_query, (instrument_id, requester_id))
    connection.commit()
    rows_affected = cursor.rowcount  # Get the number of rows affected by the delete operation
    cursor.close()

    if rows_affected > 0:
        return jsonify({"message": f"{rows_affected} loan request(s) cancelled successfully."}), 200
    else:
        return jsonify({"message": "Failed to cancel loan requests."}), 500

@loan_endpoints.route('/loan_list/<int:instrument_id>', methods=['GET'])
def get_loan_list(instrument_id):
    """Route to get all instruments requested by a specific user."""
    # Connect to the database
    connection = get_connection()
    cursor = connection.cursor()
    select_query = """
        SELECT * FROM `loanrequests` INNER JOIN users ON users.user_id = loanrequests.requester_id WHERE instrument_id = %s
    """
    cursor.execute(select_query, (instrument_id,))
    list_request = cursor.fetchall()

    cursor.close()
    connection.close()
    if not list_request:
        return jsonify({"message": "No loan requests found for this user."}), 404
       # Prepare the list of request to return
    request_list = []
    for r in list_request:
        request_data = {
            "request_id": r[0],
            "message": r[4],
            "user_id": r[5],
            "full_name": r[9],
            "request_date": r[3],
            "phone": r[10],
        }
        request_list.append(request_data)

    return jsonify({"requester_id": instrument_id, "list": request_list}), 200

# Read My Loans
@loan_endpoints.route('/my_loans/<int:requester_id>', methods=['GET'])
def get_my_loans(requester_id):
    """Route to get all instruments requested by a specific user."""
    # Connect to the database
    connection = get_connection()
    cursor = connection.cursor()

    # Query to get all instruments requested by the requester
    select_query = """
        SELECT a.request_date,
       b.location,
       c.full_name,
       c.phone,
       0 AS source
        FROM loanrequests a
        INNER JOIN instruments b ON b.instrument_id = a.instrument_id
        INNER JOIN users c ON c.user_id = b.owner_id
        WHERE a.requester_id = %s
        UNION ALL
        SELECT a.loan_date,
            b.location,
            c.full_name,
            c.phone,
            1 AS source
        FROM loans a
        INNER JOIN instruments b ON b.instrument_id = a.instrument_id
        INNER JOIN users c ON c.user_id = b.owner_id
        WHERE a.borrower_id = %s;
    """
    cursor.execute(select_query, (requester_id,requester_id))
    myLoans = cursor.fetchall()

    cursor.close()
    connection.close()

    if not myLoans:
        return jsonify({"message": "No loan requests found for this user."}), 404
    
 
    # Prepare the list of myLoans to return
    myLoans_list = []
    for loan in myLoans:
        loan_data = {
            "request_date": loan[0],
            "location": loan[1],
            "full_name": loan[2],
            "phone": loan[3],
            "source": loan[4],
        }
        myLoans_list.append(loan_data)

    return jsonify({"requester_id": requester_id, "list": myLoans_list}), 200

@loan_endpoints.route('/loan_requests/<int:requester_id>', methods=['GET'])
def get_loan_requests(requester_id):
    """Route to get all instruments requested by a specific user, including those in loans."""
    connection = get_connection()
    cursor = connection.cursor()

    # Query to get all instruments requested by the requester from loanrequests
    loanrequests_query = """
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
        FROM loanrequests lr
        JOIN instruments i ON lr.instrument_id = i.instrument_id
        JOIN users u ON i.owner_id = u.user_id
        JOIN instrument_type it ON i.instrument_type_id = it.id
        LEFT JOIN reviews r ON i.instrument_id = r.instrument_id
        WHERE lr.requester_id = %s
        GROUP BY i.instrument_id, i.owner_id, u.username, i.instrument_name, i.description, 
                 i.location, i.availability_status, i.image, i.instrument_type_id, it.name
    """
    
    # Query to get all instruments from loans where instruments.instrument_id = loans.instrument_id
    loans_query = """
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
        FROM loans l
        JOIN instruments i ON l.instrument_id = i.instrument_id
        JOIN users u ON i.owner_id = u.user_id
        JOIN instrument_type it ON i.instrument_type_id = it.id
        LEFT JOIN reviews r ON i.instrument_id = r.instrument_id
        WHERE l.borrower_id = %s
        GROUP BY i.instrument_id, i.owner_id, u.username, i.instrument_name, i.description, 
                 i.location, i.availability_status, i.image, i.instrument_type_id, it.name
    """

    cursor.execute(loanrequests_query, (requester_id,))
    loanrequests_instruments = cursor.fetchall()
    
    cursor.execute(loans_query, (requester_id,))
    loans_instruments = cursor.fetchall()

    cursor.close()
    connection.close()

    # Combine the results from both queries
    instruments = loanrequests_instruments + loans_instruments

    if not instruments:
        return jsonify({"message": "No loan requests found for this user."}), 404

    # Prepare the list of instruments to return
    instruments_list = []
    for instrument in instruments:
        instrument_data = {
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
            "average_rating": instrument[10] # Ensure average_rating is converted to float
        }
        instruments_list.append(instrument_data)

    return jsonify({"requester_id": requester_id, "instruments": instruments_list}), 200

