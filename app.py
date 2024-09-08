from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Set a secret key for session management

# Database connection setup
db_config = {
    'host': 'localhost',
    'user': 'root',          # Replace with your MySQL username
    'password': '',          # Replace with your MySQL password
    'database': 'mydatabase' # Your database name
}

# Function to get the database connection
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# Fetch available tickets and their prices from the database
def fetch_tickets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ticket_name, available, price FROM tickets")
    tickets = {row['ticket_name']: row['available'] for row in cursor}
    prices = {row['ticket_name']: row['price'] for row in cursor}
    cursor.close()
    conn.close()
    return tickets, prices

# Store booked tickets temporarily for payment processing
booked_tickets = {}

@app.route('/')
def index():
    available_tickets, ticket_prices = fetch_tickets()
    # Pass booked_tickets to the template to prevent UndefinedError
    return render_template('index.html', tickets=available_tickets, prices=ticket_prices, booked_tickets=booked_tickets)

@app.route('/book', methods=['POST'])
def book_ticket():
    ticket_type = request.form.get('ticket_type')
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT available, price FROM tickets WHERE ticket_name = %s", (ticket_type,))
    result = cursor.fetchone()

    if result and result[0] > 0:
        # Update available tickets in the database and add to booked tickets for processing payment
        cursor.execute("UPDATE tickets SET available = available - 1 WHERE ticket_name = %s", (ticket_type,))
        booked_tickets[ticket_type] = result[1]
        conn.commit()
        flash(f'Ticket booked successfully for {ticket_type}! Please proceed to payment.')
    else:
        flash(f'Sorry, {ticket_type} tickets are sold out.')

    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/cancel', methods=['POST'])
def cancel_ticket():
    ticket_type = request.form.get('ticket_type')
    conn = get_db_connection()
    cursor = conn.cursor()

    if ticket_type in booked_tickets:
        # Update available tickets and remove from booked tickets
        cursor.execute("UPDATE tickets SET available = available + 1 WHERE ticket_name = %s", (ticket_type,))
        booked_tickets.pop(ticket_type, None)
        conn.commit()
        flash(f'Ticket canceled successfully for {ticket_type}!')
    else:
        flash(f'No booked ticket found for {ticket_type}.')

    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/payment', methods=['POST'])
def payment():
    ticket_type = request.form.get('ticket_type')
    payment_amount = request.form.get('payment_amount', type=int)
    expected_amount = booked_tickets.get(ticket_type)

    if expected_amount and payment_amount == expected_amount:
        # Clear booked ticket after successful payment
        flash(f'Payment of {payment_amount} rupees successful for {ticket_type}!')
        booked_tickets.pop(ticket_type, None)
    else:
        flash(f'Payment failed! Expected amount for {ticket_type} is {expected_amount}.')

    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    ticket_type = request.form.get('ticket_type')
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT available FROM tickets WHERE ticket_name = %s", (ticket_type,))
    available = cursor.fetchone()

    if available:
        flash(f'{available[0]} tickets available for {ticket_type}.')
    else:
        flash(f'No tickets found for {ticket_type}.')

    cursor.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
