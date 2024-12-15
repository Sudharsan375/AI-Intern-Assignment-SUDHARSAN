from flask import Flask, jsonify, request
import sqlite3
from functools import wraps
import os

app = Flask(__name__)

# Set the API key (you can set this in your environment variables)
API_KEY = os.environ.get('API_KEY', 'my_secret_api_key_12345')

# Database functions
def get_db_connection():
    conn = sqlite3.connect('invoices.db')
    conn.row_factory = sqlite3.Row
    return conn

# Database setup
def init_db():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY,
            project TEXT,
            contractor_name TEXT,
            vendor_name TEXT,
            invoice_amount REAL,
            balance REAL
        )
    ''')
    conn.commit()
    conn.close()

#Error Handling
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify(error=str(e)), 500

# Input validation & API key decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if api_key != API_KEY:
            return jsonify({"error": "Unauthorized access!"}), 403
        return f(*args, **kwargs)
    return decorated_function

# Endpoint to get top invoices
@app.route('/invoices/top', methods=['GET'])
@require_api_key
def get_top_invoices():
    project = request.args.get('project')
    if not project:
        return jsonify({"error": "Project parameter is required!"}), 400
    try:
        conn = sqlite3.connect('invoices.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM invoices WHERE project = ? ORDER BY invoice_amount DESC LIMIT 5', (project,))
        top_invoices = cursor.fetchall()
        conn.close()
        if not top_invoices:
            return jsonify({"message": "No invoices found for the specified project."}), 404
        return jsonify([{
            "project": row[1],
            "contractor_name": row[2],
            "vendor_name": row[3],
            "invoice_amount": row[4],
            "balance": row[5]
        } for row in top_invoices])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to get the highest balance invoice
@app.route('/invoices/highest_balance', methods=['GET'])
@require_api_key
def get_highest_balance_invoice():
    try:
        conn = sqlite3.connect('invoices.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM invoices ORDER BY balance DESC LIMIT 1')
        highest_balance_invoice = cursor.fetchone()
        conn.close()
        if not highest_balance_invoice:
            return jsonify({"message": "No invoices found."}), 404
        return jsonify({
            "project": highest_balance_invoice[1],
            "contractor_name": highest_balance_invoice[2],
            "vendor_name": highest_balance_invoice[3],
            "invoice_amount": highest_balance_invoice[4],
            "balance": highest_balance_invoice[5]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Endpoint for searching invoices
@app.route('/invoices/search', methods=['GET'])
@require_api_key
def search_invoices():
    query = request.args.get('query')
    
    # Validate the query parameter
    if not query or len(query) < 3:
        return jsonify({"error": "Query parameter is required and must be at least 3 characters long!"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute the SQL query
        cursor.execute('SELECT * FROM invoices WHERE contractor_name LIKE ? OR vendor_name LIKE ?', ('%' + query + '%', '%' + query + '%'))
        search_results = cursor.fetchall()
        conn.close()
        
        # Check if there are results
        if not search_results:
            return jsonify({"message": "No results found for the given query."}), 404
        
        # Format the results for the response
        formatted_results = [{
            "project": row[0],          # Adjust index based on your table structure
            "contractor_name": row[1],
            "vendor_name": row[2],
            "invoice_amount": row[3],
            "balance": row[4]
        } for row in search_results]
        
        return jsonify(formatted_results), 200

    except sqlite3.Error as e:
        return jsonify({"error": "Database error: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500
    
# Endpoint to create a new invoice
@app.route('/invoices', methods=['POST'])
@require_api_key
def create_invoice():
    data = request.json
    required_fields = ["project", "contractor_name", "vendor_name", "invoice_amount", "balance"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields!"}), 400
    
    try:
        conn = sqlite3.connect('invoices.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO invoices (project, contractor_name, vendor_name, invoice_amount, balance)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['project'], data['contractor_name'], data['vendor_name'], data['invoice_amount'], data['balance']))
        conn.commit()
        conn.close()
        return jsonify({"message": "Invoice created successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Endpoint to update an invoice balance
@app.route('/invoices/update_balance/<int:invoice_id>', methods=['PUT'])
def update_invoice_balance(invoice_id):
    data = request.get_json()
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE invoices SET balance = ? WHERE id = ?', (data['balance'], invoice_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Invoice balance updated successfully'})

# Endpoint to delete an invoice
@app.route('/invoices', methods=['DELETE'])
@require_api_key
def delete_invoice():
    data = request.json
    if not all(field in data for field in ["project", "contractor_name", "vendor_name"]):
        return jsonify({"error": "Project, contractor_name, and vendor_name fields are required!"}), 400

    try:
        conn = get_db_connection()
        conn.execute('''
            DELETE FROM invoices WHERE project = ? AND contractor_name = ? AND vendor_name = ?
        ''', (data['project'], data['contractor_name'], data['vendor_name']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Invoice deleted successfully'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Endpoint to get total amount of invoices for a project
@app.route('/invoices/total_amount', methods=['GET'])
@require_api_key
def get_total_amount():
    project = request.args.get('project')
    if not project:
        return jsonify({"error": "Project parameter is required!"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(invoice_amount) AS total_amount FROM invoices WHERE project = ?', (project,))
        total_amount = cursor.fetchone()['total_amount']
        conn.close()

        if total_amount is None:
            return jsonify({"message": "No invoices found for the specified project."}), 404
        
        return jsonify({"total_amount": total_amount})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to count invoices for a contractor
@app.route('/invoices/count', methods=['GET'])
@require_api_key
def count_invoices():
    contractor_name = request.args.get('contractor_name')
    if not contractor_name:
        return jsonify({"error": "Contractor name parameter is required!"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) AS invoice_count FROM invoices WHERE contractor_name = ?', (contractor_name,))
        invoice_count = cursor.fetchone()['invoice_count']
        conn.close()

        return jsonify({"invoice_count": invoice_count})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Handling irrelevant questions
@app.route('/inquiries', methods=['GET'])
@require_api_key
def handle_inquiry():
    inquiry = request.args.get('question')
    
    if not inquiry:
        return jsonify({"error": "Question parameter is required!"}), 400
    
    irrelevant_questions = [
        "What's the current score of the match?",
        "What is the weather today?"
    ]
    
    if inquiry in irrelevant_questions:
        return jsonify({"message": "I'm sorry, but I can't help with that question. Please ask about invoices or related topics."}), 200


if __name__ == '__main__':
    init_db()
    app.run(debug=True)