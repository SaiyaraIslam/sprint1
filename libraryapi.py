from flask import Flask, request, jsonify
from flask_cors import CORS  
import mysql.connector
import bcrypt
from creds import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from datetime import datetime, timezone

app = Flask(__name__)
app.config["DEBUG"] = True

# Add this line to allow requests from Node frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})
@app.before_request
def log_request():
    print(f"📥 {request.method} {request.url} | Origin: {request.headers.get('Origin')}")

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,OPTIONS')
    return response


# defining the create connection to the sql db
def create_connection():
    try:
        return mysql.connector.connect(  # data connection info
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
    except mysql.connector.Error as e:  # debugging if runs into error
        print(f"Database connection error: {e}")
        return None


# defining fucntion to create and run the selected queries 
def execute_read_query(query, values=None):
    db = create_connection()
    if db is None:
        return {'error': 'Database connection failed'}
    try:   # try block for checking for the selected result
        cursor = db.cursor(dictionary=True)
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        return results
    except Exception as e:  # debugging if runs into error
        return {'error': str(e)}
    finally:
        cursor.close()
        db.close()


# app flask route to fetch books
@app.route('/api/books', methods=['GET', 'POST'])
def manage_books():
    conn = create_connection()  # creating the connection
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'GET':  # using the GET method
        cursor.execute("SELECT * FROM books")  # function in sql for fetching the books from db
        books = cursor.fetchall()
        conn.close()
        return jsonify(books)  # returning the fetched books
    
    elif request.method == 'POST':  # using the POST method to add books
        request_data = request.get_json()
        if not all(i in request_data for i in ('title', 'author', 'genre')):
            # returning an error block if all criteria is not met when entering info
            return jsonify({'error': 'Missing required info'}), 400

        query = "INSERT INTO books (title, author, genre, status) VALUES (%s, %s, %s, 'available')"
        # inserting the values in the query
        values = (request_data['title'], request_data['author'], request_data['genre'])
        cursor.execute(query, values)
        conn.commit() # connection to commit the changes
        conn.close()
        return jsonify({'message': 'Book added successfully'}) # sending the message when books are added successfully 


# app flask route to fetch customer info and adding new customer to the system
@app.route('/api/customers', methods=['GET', 'POST'])
def manage_customers():
    conn = create_connection() # creating the connection
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'GET': # using the GET method
        cursor.execute("SELECT id, firstname, lastname, email FROM customers") 
        # selecting the info from db
        customers = cursor.fetchall() # fetching all the info on customer 
        conn.close()
        return jsonify(customers)  # formatting the customer info into json string 
    
    elif request.method == 'POST': # using the POST method to add customers 
        request_data = request.get_json()
        password = request_data['password'].encode() # hashing the password by encoding
        # used ChatGPT in this part because originally i was not using bcrypt and running into error messages then ChatGPT suggested I import
        # bcrypt to my password hashing can be more secure, and have fixed length and also by using the gensalt() statement 
        password_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        query = "INSERT INTO customers (firstname, lastname, email, passwordhash) VALUES (%s, %s, %s, %s)"
        # inserting the values into the correct places in the query
        values = (request_data['firstname'], request_data['lastname'], request_data['email'], password_hash)
        cursor.execute(query, values) # executing the values and new query  result
        conn.commit() # connection to commit the changes
        conn.close()
        return jsonify({'message': 'Customer added successfully'}) # sending the message when customers are added successfully 

# app flask route for customers to borrow their selected books
@app.route('/api/borrow', methods=['POST'])
def borrow_book(): # defining the borrow books statement
    request_data = request.get_json()
    conn = create_connection()  # creating the connection
    cursor = conn.cursor(dictionary=True)
# checking to see if the customer already exists in the db
    cursor.execute("SELECT id FROM customers WHERE id = %s", (request_data['customerid'],))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Customer does not exist'}), 400  # error message if the customer doesn't exist
# checking to see if the book is available for borrowing 
    cursor.execute("SELECT * FROM books WHERE id = %s AND status = 'available'", (request_data['bookid'],))
    book = cursor.fetchone()
    if not book:
        conn.close() # if the book is not available then sending an error message 
        return jsonify({'error': 'Book is not available'}), 400
# took help from ChatGPT on this part originally I wasn't checking to see if the customer had another book borrowed under their name 
# ChatGPT suggested I use return date and request_data to ensure I don't get the wrong error message 
    cursor.execute("SELECT * FROM borrowing_records WHERE customerid = %s AND returndate IS NULL", (request_data['customerid'],))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Customer already has a borrowed book'}), 400  # sending an error message if the customer has already borrowed a book

    query = "INSERT INTO borrowing_records (bookid, customerid, borrowdate) VALUES (%s, %s, %s)"
    values = (request_data['bookid'], request_data['customerid'], datetime.now(timezone.utc))
# took help from ChatGPT on this part because I didn't know what timezone function to use, and chatgpt suggested I use timezone.utc and import timezone along with datetime
    cursor.execute(query, values)
    cursor.execute("UPDATE books SET status = 'unavailable' WHERE id = %s", (request_data['bookid'],))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Book borrowed successfully'})

# flask route to show the borrowings records
@app.route('/api/borrowings', methods=['GET']) # using the GET method 
def get_borrowings(): 
    query = """
    SELECT br.id, b.title, c.firstname, c.lastname, br.borrowdate, br.returndate, br.late_fee
    FROM borrowing_records br
    JOIN books b ON br.bookid = b.id
    JOIN customers c ON br.customerid = c.id
    """
# took help from ChatGPT on this part because I wasn't initiating a query, and ChatGPT suggested I use alias for borrowing records as br,
# books as in b, and c for customers along with aligning the record details 
    results = execute_read_query(query)
    return jsonify(results)

# flask app route to return customer info when a book is returned and it's late fee if it occurs
@app.route('/api/return', methods=['PUT'])
def return_book():
    request_data = request.get_json()
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Checking to see if borrowing record exists
    cursor.execute("SELECT * FROM borrowing_records WHERE id = %s", (request_data['id'],))
    borrowing = cursor.fetchone()
    if not borrowing:
        conn.close()
        return jsonify({'error': 'Borrowing record not found'}), 404 # error message if the record is not in the system

    # Calculate the late fee based on the right use of timezone I got using ChatGPT originally I was using UTC and it was showing with a strike on it
    # ChatGPT suggested it was because utc was deprecated and suggested to use timezone 
    returndate = datetime.now(timezone.utc)
    borrow_date = borrowing['borrowdate']
    # ChatGPT suggested I add an if statement originally was not adding it was getting error message because it was not able to calculate the time right way
    if borrow_date.tzinfo is None:
        borrow_date = borrow_date.replace(tzinfo=timezone.utc)
    overdue_days = max(0, (returndate - borrow_date).days - 10)  # 1 dollar late fee per day after 10 days
    late_fee = overdue_days * 1  # 1 dollar late fee per day if the book is overdue 

    # Updating the database with the right return date and late fee
    cursor.execute("UPDATE borrowing_records SET returndate = %s, late_fee = %s WHERE id = %s",
                   (returndate, late_fee, request_data['id']))
    cursor.execute("UPDATE books SET status = 'available' WHERE id = %s", (borrowing['bookid'],))
    conn.commit()
    conn.close()

    # Returning  success response with the late fee
    return jsonify({
        'message': 'Book returned successfully',
        'late_fee': late_fee
    })

# to run the flask app
if __name__ == '__main__':
    app.run(debug=True)