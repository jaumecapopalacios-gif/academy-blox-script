import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "academy-blox-secret"


DATABASE = "academy.db"


LESSONS = [
    {
        "title": "Introducción a Roblox Studio",
        "description": "Aprende las bases de Roblox Studio."
    },
    {
        "title": "Primer Script en Luau",
        "description": "Aprende a programar en Roblox."
    },
    {
        "title": "Variables",
        "description": "Aprende variables en Luau."
    }
]


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():

    db = get_db()

    db.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    db.commit()
    db.close()


init_db()


def current_user():

    if "user_id" not in session:
        return None

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    db.close()

    return user



@app.route("/")
def index():

    user = current_user()

    if not user:
        return redirect(url_for("login"))

    return render_template(
        "index.html",
        user=user,
        lessons=LESSONS
    )



@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        db = get_db()

        password_hash = generate_password_hash(password)

        try:

            db.execute(
                "INSERT INTO users(email,password) VALUES(?,?)",
                (email,password_hash)
            )

            db.commit()

        except:

            flash("Ese usuario ya existe.")

            return redirect(
                url_for("register")
            )

        db.close()

        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )



@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]


        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        db.close()


        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            return redirect(
                url_for("index")
            )


        flash("Datos incorrectos.")


    return render_template(
        "login.html"
    )



@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )



@app.route("/lesson/<int:number>")
def lesson(number):

    user = current_user()

    if not user:
        return redirect(
            url_for("login")
        )

    return render_template(
        "lesson.html",
        lesson=LESSONS[number-1]
    )



if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )
