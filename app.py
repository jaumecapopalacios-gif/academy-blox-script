import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "academy-blox-secret"
)


DATABASE = "academy.db"

ADMIN_CODE = "BLOX-ADMIN-9382"


LESSONS = [
    {
        "title": "Introducción a Roblox Studio",
        "description": "Aprende las bases de Roblox Studio."
    },
    {
        "title": "Primer Script en Luau",
        "description": "Crea tus primeros scripts."
    },
    {
        "title": "Sistemas avanzados",
        "description": "Aprende sistemas para juegos."
    }
]


def db():
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    return con



def setup():

    con = db()

    con.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        admin INTEGER DEFAULT 0
    )
    """)

    con.commit()
    con.close()



setup()



def user():

    if "id" not in session:
        return None

    con = db()

    result = con.execute(
        "SELECT * FROM users WHERE id=?",
        (session["id"],)
    ).fetchone()

    con.close()

    return result



@app.route("/")
def home():

    u = user()

    if not u:
        return redirect("/login")

    return render_template(
        "index.html",
        user=u,
        lessons=LESSONS
    )



@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        email=request.form["email"]
        password=request.form["password"]

        con=db()

        try:
            con.execute(
                "INSERT INTO users(email,password) VALUES(?,?)",
                (
                    email,
                    generate_password_hash(password)
                )
            )

            con.commit()

        except:

            flash("Usuario ya existe")
            return redirect("/register")


        con.close()

        return redirect("/login")


    return render_template("register.html")



@app.route("/login", methods=["GET","POST"])
def login():

    if request.method=="POST":

        email=request.form["email"]
        password=request.form["password"]

        con=db()

        u=con.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        con.close()


        if u and check_password_hash(u["password"],password):

            session["id"]=u["id"]

            return redirect("/")


        flash("Datos incorrectos")


    return render_template("login.html")



@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")



@app.route("/admin")
def admin():

    u=user()

    if not u or u["admin"]!=1:
        return redirect("/")


    con=db()

    users=con.execute(
        "SELECT * FROM users"
    ).fetchall()

    con.close()


    return render_template(
        "admin.html",
        users=users
    )



@app.route("/activate-admin",methods=["POST"])
def activate_admin():

    u=user()

    if not u:
        return redirect("/login")


    code=request.form["code"]


    if code==ADMIN_CODE:

        con=db()

        con.execute(
            "UPDATE users SET admin=1 WHERE id=?",
            (u["id"],)
        )

        con.commit()
        con.close()


    return redirect("/")



@app.route("/ai")
def ai():

    if not user():
        return redirect("/login")

    return render_template("ai.html")



@app.route("/ai/chat",methods=["POST"])
def ai_chat():

    data=request.json

    return jsonify({
        "answer":
        "Academy AI está conectada. Próximamente responderá preguntas de Roblox Studio."
    })



if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT",5000))
    )
