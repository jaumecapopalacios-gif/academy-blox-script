import os
import sqlite3
from datetime import date

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


try:
    from openai import OpenAI
except ImportError:
    OpenAI = None



app = Flask(__name__)


app.secret_key = os.environ.get(
    "SECRET_KEY",
    "academy-blox-secret"
)



DATABASE = "academy.db"



ADMIN_CODE = os.environ.get(
    "ADMIN_CODE",
    "BLOX-ADMIN-9382"
)



OPENAI_API_KEY = os.environ.get(
    "OPENAI_API_KEY"
)



AI_LIMIT = 10



ai_client = None


if OPENAI_API_KEY and OpenAI:

    try:
        ai_client = OpenAI(
            api_key=OPENAI_API_KEY
        )

    except Exception:

        ai_client = None





LESSONS = [

    {
        "title": "Introducción a Roblox Studio",
        "description": "Aprende los conceptos básicos.",
        "content": """
Roblox Studio permite crear juegos y experiencias.

Puedes crear mapas, sistemas y scripts.
"""
    },


    {
        "title": "Primer Script Luau",
        "description": "Aprende tu primer código.",
        "content": """
Ejemplo:

print("Hola Roblox")
"""
    },


    {
        "title": "Variables",
        "description": "Guarda información con variables.",
        "content": """
Ejemplo:

local monedas = 100
"""
    }

]





def db():

    con = sqlite3.connect(
        DATABASE
    )

    con.row_factory = sqlite3.Row

    return con





def init_db():

    con = db()


    con.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        email TEXT UNIQUE,

        password TEXT,

        is_admin INTEGER DEFAULT 0

    )
    """)


    con.commit()

    con.close()





init_db()





def current_user():


    if "user_id" not in session:

        return None


    con = db()


    user = con.execute(

        "SELECT * FROM users WHERE id=?",

        (
            session["user_id"],
        )

    ).fetchone()


    con.close()


    return user






def logged():

    return "user_id" in session
    @app.route("/")
def index():

    if not logged():

        return redirect(
            url_for("login")
        )


    return render_template(
        "index.html",
        lessons=LESSONS,
        current_user=current_user()
    )





@app.route("/register", methods=["GET", "POST"])
def register():


    if request.method == "POST":


        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        if not email or not password:

            flash(
                "Completa todos los campos"
            )

            return redirect(
                url_for("register")
            )



        con = db()


        existe = con.execute(

            "SELECT id FROM users WHERE email=?",

            (
                email,
            )

        ).fetchone()



        if existe:

            con.close()

            flash(
                "Ese correo ya existe"
            )

            return redirect(
                url_for("register")
            )



        password_hash = generate_password_hash(
            password
        )



        con.execute(

            """
            INSERT INTO users(email,password)
            VALUES(?,?)
            """,

            (
                email,
                password_hash
            )

        )


        con.commit()

        con.close()


        flash(
            "Cuenta creada"
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



        con = db()



        user = con.execute(

            "SELECT * FROM users WHERE email=?",

            (
                email,
            )

        ).fetchone()



        con.close()



        if not user:


            flash(
                "Datos incorrectos"
            )

            return redirect(
                url_for("login")
            )



        if not check_password_hash(

            user["password"],

            password

        ):


            flash(
                "Datos incorrectos"
            )

            return redirect(
                url_for("login")
            )



        session["user_id"] = user["id"]



        return redirect(
            url_for("index")
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





@app.route("/lesson/<int:number>")
def lesson(number):

    if not logged():

        return redirect(
            url_for("login")
        )


    if number < 1 or number > len(LESSONS):

        return "Lección no encontrada", 404


    return render_template(
        "lesson.html",
        lesson=LESSONS[number-1],
        current_user=current_user()
    )






@app.route("/activate-admin", methods=["POST"])
def activate_admin():


    if not logged():

        return redirect(
            url_for("login")
        )



    code = request.form.get(
        "admin_code",
        ""
    )



    if code != ADMIN_CODE:


        flash(
            "Código incorrecto"
        )


        return redirect(
            url_for("index")
        )



    user = current_user()



    con = db()



    con.execute(

        """
        UPDATE users
        SET is_admin=1
        WHERE id=?
        """,

        (
            user["id"],
        )

    )



    con.commit()

    con.close()



    flash(
        "Administrador activado"
    )


    return redirect(
        url_for("index")
    )







@app.route("/admin")
def admin():


    if not logged():

        return redirect(
            url_for("login")
        )



    user = current_user()



    if not user["is_admin"]:


        flash(
            "No tienes permisos"
        )


        return redirect(
            url_for("index")
        )



    con = db()



    users = con.execute(

        "SELECT * FROM users"

    ).fetchall()



    con.close()



    return render_template(

        "admin.html",

        users=users,

        current_user=user

    )
    @app.route("/admin/console", methods=["POST"])
def admin_console():


    if not logged():

        return redirect(
            url_for("login")
        )


    user = current_user()


    if not user["is_admin"]:

        return redirect(
            url_for("index")
        )



    command = request.form.get(
        "command",
        ""
    ).strip()



    parts = command.split()



    if not parts:

        flash(
            "Escribe un comando"
        )

        return redirect(
            url_for("admin")
        )



    action = parts[0].lower()



    con = db()



    if action == "users":


        users = con.execute(

            "SELECT email,is_admin FROM users"

        ).fetchall()



        for u in users:

            flash(
                f'{u["email"]} Admin:{u["is_admin"]}'
            )



    elif action == "makeadmin" and len(parts) > 1:


        con.execute(

            """
            UPDATE users
            SET is_admin=1
            WHERE email=?
            """,

            (
                parts[1],
            )

        )

        flash(
            "Administrador creado"
        )



    elif action == "delete" and len(parts) > 1:


        con.execute(

            """
            DELETE FROM users
            WHERE email=?
            """,

            (
                parts[1],
            )

        )


        flash(
            "Usuario eliminado"
        )



    else:

        flash(
            "Comandos: users, makeadmin correo, delete correo"
        )



    con.commit()

    con.close()



    return redirect(
        url_for("admin")
    )







# =========================
# ACADEMY AI
# =========================


@app.route("/ai")
def ai():


    if not logged():

        return redirect(
            url_for("login")
        )


    return render_template(
        "ai.html"
    )






@app.route("/ai/chat", methods=["POST"])
def ai_chat():


    if not logged():

        return jsonify(
            {
                "error":"No conectado"
            }
        )



    data = request.json



    question = data.get(
        "question",
        ""
    )



    if ai_client is None:


        return jsonify(

            {
                "answer":
                "La IA no está configurada todavía."
            }

        )



    try:


        response = ai_client.responses.create(

            model="gpt-5.6-luna",

            input=question

        )



        return jsonify(

            {
                "answer":
                response.output_text
            }

        )


    except Exception:


        return jsonify(

            {
                "answer":
                "Error conectando con la IA."
            }

        )







if __name__ == "__main__":


    port = int(

        os.environ.get(
            "PORT",
            5000
        )

    )


    app.run(

        host="0.0.0.0",

        port=port

    )
