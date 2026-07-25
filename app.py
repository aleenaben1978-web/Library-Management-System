from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import db, cursor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.secret_key = "library_management_secure_key_2026_random"
Talisman(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        # Find user by email
        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):

            session["user_id"] = user[0]
            session["user_email"] = user[2]
            session["role"] = user[4]

            return render_template("dashboard.html")

        else:
            return "Invalid Email or Password!"

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
       password = generate_password_hash(request.form["password"])

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            return "This email is already registered."

        # Save new user
        cursor.execute(
            INSERT INTO users (name, email, password, role)
            VALUES (%s, %s, %s, %s)
           (name, email, password, "user")
        )

        db.commit()

        return redirect(url_for("login"))

    return render_template("register.html")
@app.route("/books", methods=["GET", "POST"])
def books():
    if "user_id" not in session:
    return redirect(url_for("login"))
    if request.method == "POST":

        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        quantity = request.form["quantity"]

        # Check if ISBN already exists
        cursor.execute("SELECT * FROM books WHERE isbn=%s", (isbn,))
        existing_book = cursor.fetchone()

        if existing_book:
            flash("This ISBN already exists. Please use a different ISBN.", "danger")
            return redirect(url_for("books"))

        cursor.execute(
            """
            INSERT INTO books (title, author, isbn, quantity)
            VALUES (%s, %s, %s, %s)
            """,
            (title, author, isbn, quantity)
        )

        db.commit()

        flash("Book added successfully!", "success")
        return redirect(url_for("books"))

    return render_template("add_book.html")
@app.route("/view_books")
def view_books():

    search = request.args.get("search")

    if search:

        cursor.execute(
            """
            SELECT * FROM books
            WHERE title LIKE %s OR author LIKE %s
            """,
            ('%' + search + '%', '%' + search + '%')
        )

    else:

        cursor.execute("SELECT * FROM books")

    books = cursor.fetchall()

    return render_template("view_books.html", books=books)
@app.route("/delete_book/<int:id>")
def delete_book(id):
    if session.get("role") != "admin":
    return "Access denied. Admins only."

    cursor.execute("DELETE FROM books WHERE id=%s", (id,))
    db.commit()

    return redirect(url_for("view_books"))
@app.route("/edit_book/<int:id>", methods=["GET", "POST"])
def edit_book(id):

    if request.method == "POST":

        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        quantity = request.form["quantity"]

        cursor.execute(
            """
            UPDATE books
            SET title=%s, author=%s, isbn=%s, quantity=%s
            WHERE id=%s
            """,
            (title, author, isbn, quantity, id)
        )

        db.commit()

        return redirect(url_for("view_books"))

    cursor.execute("SELECT * FROM books WHERE id=%s", (id,))
    book = cursor.fetchone()

    return render_template("edit_book.html", book=book)
@app.route("/students", methods=["GET", "POST"])
def students():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]

        # Check if email already exists
        cursor.execute("SELECT * FROM students WHERE email=%s", (email,))
        existing_student = cursor.fetchone()

        if existing_student:
            return "This email is already registered."

        cursor.execute(
            """
            INSERT INTO students (name, email, phone)
            VALUES (%s, %s, %s)
            """,
            (name, email, phone)
        )

        db.commit()

        return redirect(url_for("students"))

    return render_template("add_student.html")
@app.route("/view_students")
def view_students():

    search = request.args.get("search")

    if search:

        cursor.execute(
            """
            SELECT * FROM students
            WHERE name LIKE %s OR email LIKE %s
            """,
            ('%' + search + '%', '%' + search + '%')
        )

    else:

        cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()

    return render_template("view_students.html", students=students)
@app.route("/edit_student/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]

        cursor.execute(
            """
            UPDATE students
            SET name=%s, email=%s, phone=%s
            WHERE id=%s
            """,
            (name, email, phone, id)
        )

        db.commit()

        return redirect(url_for("view_students"))

    cursor.execute("SELECT * FROM students WHERE id=%s", (id,))
    student = cursor.fetchone()

    return render_template("edit_student.html", student=student)
@app.route("/delete_student/<int:id>")
def delete_student(id):

    cursor.execute("DELETE FROM students WHERE id=%s", (id,))
    db.commit()

    return redirect(url_for("view_students"))


@app.route("/issue", methods=["GET", "POST"])
def issue():

    if request.method == "POST":

        student_id = request.form["student_id"]
        book_id = request.form["book_id"]

        # Check available quantity
        cursor.execute("SELECT quantity FROM books WHERE id=%s", (book_id,))
        book = cursor.fetchone()

        if book[0] <= 0:
            return "Book is out of stock!"

        # Issue the book
        cursor.execute(
            """
            INSERT INTO issued_books (student_id, book_id, issue_date)
            VALUES (%s, %s, CURDATE())
            """,
            (student_id, book_id)
        )

        # Reduce quantity by 1
        cursor.execute(
            """
            UPDATE books
            SET quantity = quantity - 1
            WHERE id=%s
            """,
            (book_id,)
        )

        db.commit()

        return redirect(url_for("issue"))

    # Load students
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()

    # Load books with quantity > 0
    cursor.execute("SELECT id, title FROM books WHERE quantity > 0")
    books = cursor.fetchall()

    return render_template(
        "issue_book.html",
        students=students,
        books=books
    )
try:
    cursor.execute("SELECT DATABASE();")
    print("Connected to:", cursor.fetchone())
except Exception as e:
    print("Connection failed:", e)
@app.route("/issued_books")
def issued_books():

    cursor.execute("""
        SELECT
            issued_books.id,
            students.name,
            books.title,
            issued_books.issue_date,
            issued_books.return_date
        FROM issued_books
        JOIN students ON issued_books.student_id = students.id
        JOIN books ON issued_books.book_id = books.id
    """)

    issued = cursor.fetchall()

    return render_template("issued_books.html", issued=issued)
@app.route("/return_book/<int:id>")
def return_book(id):

    # Get the book ID
    cursor.execute(
        "SELECT book_id FROM issued_books WHERE id=%s",
        (id,)
    )
    issued = cursor.fetchone()

    # Update return date
    cursor.execute(
        "UPDATE issued_books SET return_date = CURDATE() WHERE id=%s",
        (id,)
    )

    # Increase book quantity
    cursor.execute(
        "UPDATE books SET quantity = quantity + 1 WHERE id=%s",
        (issued[0],)
    )

    db.commit()

    return redirect(url_for("issued_books"))
if __name__ == "__main__":
    app.run(debug=True)