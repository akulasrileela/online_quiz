from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
)
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import uuid
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


app = Flask(__name__)

app.secret_key = "change-this-secret-key"

DATABASE = "quiz.db"


# =========================================================
# QUESTIONS
# =========================================================

QUESTIONS = {

    "Python": [

        (
            "Which keyword is used to define a function in Python?",
            ["func", "define", "def", "function"],
            "def"
        ),

        (
            "Which data type is used to store True or False?",
            ["int", "bool", "str", "float"],
            "bool"
        ),

        (
            "Which symbol is used for comments in Python?",
            ["//", "#", "/*", "--"],
            "#"
        ),

        (
            "Which function is used to display output?",
            ["input()", "print()", "output()", "display()"],
            "print()"
        ),

        (
            "Which collection is ordered and changeable?",
            ["Tuple", "Set", "List", "String"],
            "List"
        )

    ],


    "Java": [

        (
            "Which keyword is used to create a class?",
            ["class", "Class", "define", "struct"],
            "class"
        ),

        (
            "Which method is the starting point of a Java program?",
            ["start()", "main()", "run()", "begin()"],
            "main()"
        ),

        (
            "Which symbol ends a Java statement?",
            [".", ":", ";", ","],
            ";"
        ),

        (
            "Which type stores whole numbers?",
            ["float", "String", "int", "boolean"],
            "int"
        ),

        (
            "Which keyword is used to inherit a class?",
            ["inherits", "extends", "implements", "super"],
            "extends"
        )

    ],


    "C": [

        (
            "Which function is the entry point of a C program?",
            ["start()", "main()", "begin()", "run()"],
            "main()"
        ),

        (
            "Which symbol is used to end a statement in C?",
            [".", ";", ":", ","],
            ";"
        ),

        (
            "Which header file is commonly used for printf()?",
            ["math.h", "string.h", "stdio.h", "stdlib.h"],
            "stdio.h"
        ),

        (
            "Which data type stores integers?",
            ["float", "int", "char", "double"],
            "int"
        ),

        (
            "Which symbol is used for a single-line comment in modern C?",
            ["//", "#", "--", "/*"],
            "//"
        )

    ],


    "C++": [

        (
            "Which keyword is used to define a class?",
            ["class", "Class", "structclass", "define"],
            "class"
        ),

        (
            "Which function is the entry point of a C++ program?",
            ["start()", "main()", "run()", "execute()"],
            "main()"
        ),

        (
            "Which operator is used for output with cout?",
            ["<<", ">>", "==", "=>"],
            "<<"
        ),

        (
            "Which header is commonly used for cout?",
            ["stdio.h", "iostream", "string.h", "stdlib.h"],
            "iostream"
        ),

        (
            "Which concept allows multiple functions with the same name?",
            ["Inheritance", "Encapsulation", "Overloading", "Abstraction"],
            "Overloading"
        )

    ],


    "JavaScript": [

        (
            "Which keyword can declare a variable in JavaScript?",
            ["var", "variable", "define", "int"],
            "var"
        ),

        (
            "Which method prints something to the browser console?",
            ["print()", "console.log()", "write()", "display()"],
            "console.log()"
        ),

        (
            "Which symbol is used for strict equality?",
            ["=", "==", "===", "!="],
            "==="
        ),

        (
            "Which type represents true or false?",
            ["String", "Boolean", "Number", "Object"],
            "Boolean"
        ),

        (
            "Which keyword declares a constant?",
            ["constant", "const", "fixed", "letconst"],
            "const"
        )

    ],


    "C#": [

        (
            "Which keyword is used to define a class in C#?",
            ["class", "Class", "define", "struct"],
            "class"
        ),

        (
            "Which method is commonly the entry point?",
            ["Start()", "Main()", "Run()", "Begin()"],
            "Main()"
        ),

        (
            "Which symbol ends a C# statement?",
            [".", ":", ";", ","],
            ";"
        ),

        (
            "Which type stores whole numbers?",
            ["float", "string", "int", "bool"],
            "int"
        ),

        (
            "Which keyword is used for inheritance?",
            ["extends", "inherits", ":", "implements"],
            ":"
        )

    ]

}


# =========================================================
# DATABASE
# =========================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_db()

    # -------------------------
    # USERS TABLE
    # -------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)


    # -------------------------
    # RESULTS TABLE
    # -------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            language TEXT NOT NULL,
            correct INTEGER NOT NULL,
            incorrect INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            certificate_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # -------------------------
    # QUESTION ANSWERS TABLE
    # -------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS question_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER NOT NULL,
            question_number INTEGER NOT NULL,
            question TEXT NOT NULL,
            selected_answer TEXT,
            correct_answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            FOREIGN KEY (result_id) REFERENCES results(id)
        )
    """)


    conn.commit()

    conn.close()


# =========================================================
# LOGIN / REGISTER
# =========================================================

@app.route("/")
def index():

    if "user_id" in session:
        return redirect(url_for("home"))

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        if not name or not email or not password:

            flash("Please fill all fields.")

            return redirect(
                url_for("register")
            )


        conn = get_db()


        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()


        if existing_user:

            conn.close()

            flash("Email already registered.")

            return redirect(
                url_for("login")
            )


        hashed_password = generate_password_hash(
            password
        )


        conn.execute(
            """
            INSERT INTO users
            (name, email, password)
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                hashed_password
            )
        )


        conn.commit()

        conn.close()


        flash(
            "Registration successful. Please login."
        )


        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        conn = get_db()


        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()


        conn.close()


        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["name"] = user["name"]

            session["email"] = user["email"]


            return redirect(
                url_for("home")
            )


        flash(
            "Invalid email or password."
        )


    return render_template(
        "login.html"
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# HOME
# =========================================================

@app.route("/home")
def home():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    languages = list(
        QUESTIONS.keys()
    )


    return render_template(
        "home.html",
        languages=languages
    )


# =========================================================
# QUIZ
# =========================================================

@app.route(
    "/quiz/<language>",
    methods=["GET", "POST"]
)
def quiz(language):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if language not in QUESTIONS:

        return "Language not found", 404


    questions = QUESTIONS[language]


    # -------------------------
    # SHOW QUIZ
    # -------------------------

    if request.method == "GET":

        return render_template(
            "quiz.html",
            language=language,
            questions=questions
        )


    # -------------------------
    # PROCESS QUIZ
    # -------------------------

    correct = 0

    submitted_answers = []


    for i, question in enumerate(questions):

        selected_answer = request.form.get(
            f"q{i}"
        )


        question_text = question[0]

        correct_answer = question[2]


        is_correct = (
            selected_answer == correct_answer
        )


        if is_correct:

            correct += 1


        submitted_answers.append({

            "question_number": i + 1,

            "question": question_text,

            "selected_answer": selected_answer,

            "correct_answer": correct_answer,

            "is_correct": is_correct

        })


    total = len(questions)

    incorrect = total - correct


    percentage = round(
        (correct / total) * 100,
        2
    )


    certificate_id = (
        "CERT-" +
        uuid.uuid4().hex[:10].upper()
    )


    # -------------------------
    # SAVE RESULT
    # -------------------------

    conn = get_db()


    cursor = conn.execute(
        """
        INSERT INTO results
        (
            user_id,
            language,
            correct,
            incorrect,
            score,
            total,
            percentage,
            certificate_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            language,
            correct,
            incorrect,
            correct,
            total,
            percentage,
            certificate_id,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )


    # IMPORTANT:
    # Get the ID of the result we just inserted.

    result_id = cursor.lastrowid


    # -------------------------
    # SAVE EACH ANSWER
    # -------------------------

    for answer in submitted_answers:

        conn.execute(
            """
            INSERT INTO question_answers
            (
                result_id,
                question_number,
                question,
                selected_answer,
                correct_answer,
                is_correct
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                result_id,
                answer["question_number"],
                answer["question"],
                answer["selected_answer"],
                answer["correct_answer"],
                1 if answer["is_correct"]
                else 0
            )
        )


    conn.commit()

    conn.close()


    return redirect(
        url_for(
            "result",
            result_id=result_id
        )
    )


# =========================================================
# RESULT
# =========================================================

@app.route("/result/<int:result_id>")
def result(result_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    conn = get_db()


    result_data = conn.execute(
        """
        SELECT
            results.*,
            users.name,
            users.email
        FROM results
        JOIN users
            ON users.id = results.user_id
        WHERE results.id = ?
        AND results.user_id = ?
        """,
        (
            result_id,
            session["user_id"]
        )
    ).fetchone()


    conn.close()


    if not result_data:

        return "Result not found", 404


    return render_template(
        "result.html",
        result=result_data
    )


# =========================================================
# QUESTION REVIEW
# =========================================================

@app.route("/review/<int:result_id>")
def review(result_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    conn = get_db()


    result_data = conn.execute(
        """
        SELECT
            results.*,
            users.name
        FROM results
        JOIN users
            ON users.id = results.user_id
        WHERE results.id = ?
        AND results.user_id = ?
        """,
        (
            result_id,
            session["user_id"]
        )
    ).fetchone()


    if not result_data:

        conn.close()

        return "Result not found", 404


    answers = conn.execute(
        """
        SELECT *
        FROM question_answers
        WHERE result_id = ?
        ORDER BY question_number
        """,
        (result_id,)
    ).fetchall()


    conn.close()


    return render_template(
        "review.html",
        result=result_data,
        answers=answers
    )


# =========================================================
# LEADERBOARD
# =========================================================

@app.route("/leaderboard")
def leaderboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    language = request.args.get(
        "language",
        "All"
    )


    conn = get_db()


    if language == "All":

        results = conn.execute(
            """
            SELECT
                results.*,
                users.name
            FROM results
            JOIN users
                ON users.id = results.user_id
            ORDER BY
                results.percentage DESC,
                results.score DESC,
                results.created_at ASC
            LIMIT 100
            """
        ).fetchall()


    else:

        results = conn.execute(
            """
            SELECT
                results.*,
                users.name
            FROM results
            JOIN users
                ON users.id = results.user_id
            WHERE results.language = ?
            ORDER BY
                results.percentage DESC,
                results.score DESC,
                results.created_at ASC
            LIMIT 100
            """,
            (language,)
        ).fetchall()


    conn.close()


    languages = list(
        QUESTIONS.keys()
    )


    return render_template(
        "leaderboard.html",
        results=results,
        languages=languages,
        selected_language=language
    )


# =========================================================
# MY RESULTS
# =========================================================

@app.route("/my-results")
def my_results():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    conn = get_db()


    results = conn.execute(
        """
        SELECT *
        FROM results
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()


    conn.close()


    return render_template(
        "my_result.html",
        results=results
    )


# =========================================================
# ADMIN / PARTICIPANT RESULTS
# =========================================================

@app.route("/admin-results")
def admin_results():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    conn = get_db()


    results = conn.execute(
        """
        SELECT
            results.*,
            users.name,
            users.email
        FROM results
        JOIN users
            ON users.id = results.user_id
        ORDER BY results.created_at DESC
        """
    ).fetchall()


    conn.close()


    return render_template(
        "admin_results.html",
        results=results
    )


# =========================================================
# CERTIFICATE
# =========================================================

@app.route("/certificate/<int:result_id>")
def certificate(result_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    conn = get_db()


    result_data = conn.execute(
        """
        SELECT
            results.*,
            users.name
        FROM results
        JOIN users
            ON users.id = results.user_id
        WHERE results.id = ?
        AND results.user_id = ?
        """,
        (
            result_id,
            session["user_id"]
        )
    ).fetchone()


    conn.close()


    if not result_data:

        return "Result not found", 404


    buffer = io.BytesIO()


    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )


    width, height = A4


    pdf.setFont(
        "Helvetica-Bold",
        26
    )


    pdf.drawCentredString(
        width / 2,
        height - 150,
        "CERTIFICATE OF PARTICIPATION"
    )


    pdf.setFont(
        "Helvetica",
        16
    )


    pdf.drawCentredString(
        width / 2,
        height - 220,
        "This certificate is proudly presented to"
    )


    pdf.setFont(
        "Helvetica-Bold",
        24
    )


    pdf.drawCentredString(
        width / 2,
        height - 270,
        result_data["name"]
    )


    pdf.setFont(
        "Helvetica",
        16
    )


    pdf.drawCentredString(
        width / 2,
        height - 330,
        f"for participating in the {result_data['language']} Quiz"
    )


    pdf.drawCentredString(
        width / 2,
        height - 370,
        f"Score: {result_data['score']} / {result_data['total']}"
    )


    pdf.drawCentredString(
        width / 2,
        height - 400,
        f"Percentage: {result_data['percentage']}%"
    )


    pdf.setFont(
        "Helvetica",
        12
    )


    pdf.drawCentredString(
        width / 2,
        height - 460,
        f"Certificate ID: {result_data['certificate_id']}"
    )


    pdf.save()


    buffer.seek(0)


    return send_file(
        buffer,
        as_attachment=True,
        download_name="quiz_certificate.pdf",
        mimetype="application/pdf"
    )


# =========================================================
# START APPLICATION
# =========================================================

# Initialize database when the application starts.

init_db()


if __name__ == "__main__":

    app.run(
        debug=True
    )