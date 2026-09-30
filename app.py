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
    "academy-blox-secret-key"
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
        "id": 1,
        "title": "Introducción a Roblox Studio",
        "description": "Aprende las bases de Roblox Studio.",
        "content": """
Roblox Studio permite crear experiencias,
mapas y videojuegos usando Luau.
"""
    },

    {
        "id": 2,
        "title": "Primer Script en Luau",
        "description": "Aprende tu primer código.",
        "content": """
Ejemplo:

print("Hola Roblox")
"""
    },

    {
        "id": 3,
        "title": "Variables",
        "description": "Guarda información en tus scripts.",
        "content": """
Ejemplo:

local monedas = 100

print(monedas)
"""
    },

    {
        "id": 4,
        "title": "Eventos",
        "description": "Haz que los objetos reaccionen.",
        "content": """
Ejemplo:

part.Touched:Connect(function()
    print("Tocado")
end)
"""
    }

]



def db():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection




def init_database():

    connection = db()


    connection.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        is_admin INTEGER DEFAULT 0,

        created TEXT

    )
    """)


    connection.execute("""
    CREATE TABLE IF NOT EXISTS ai_usage(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        day TEXT,

        amount INTEGER DEFAULT 0

    )
    """)


    connection.commit()

    connection.close()



init_database()




def current_user():

    user_id = session.get(
        "user_id"
    )

    if not user_id:
        return None


    connection = db()


    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id=?
        """,
        (user_id,)
    ).fetchone()


    connection.close()

    return user




def logged():

    return "user_id" in session
    @app.route("/")
def home():

    if not logged():

        return redirect(
            url_for("login")
        )


    return render_template(
        "index.html",
        lessons=LESSONS,
        current_user=current_user()
    )




@app.route(
    "/register",
    methods=["GET","POST"]
)
def register():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).lower().strip()


        password = request.form.get(
            "password",
            ""
        )


        if not email or not password:

            flash(
                "Completa todos los datos"
            )

            return redirect(
                url_for("register")
            )


        connection = db()


        try:

            connection.execute(
                """
                INSERT INTO users
                (
                    email,
                    password,
                    created
                )
                VALUES
                (?,?,?)
                """,
                (
                    email,
                    generate_password_hash(password),
                    str(date.today())
                )
            )


            connection.commit()


        except:

            connection.close()

            flash(
                "El usuario ya existe"
            )

            return redirect(
                url_for("register")
            )


        connection.close()


        flash(
            "Cuenta creada"
        )


        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )





@app.route(
    "/login",
    methods=["GET","POST"]
)
def login():

    if request.method == "POST":


        email = request.form.get(
            "email",
            ""
        ).lower().strip()


        password = request.form.get(
            "password",
            ""
        )


        connection = db()


        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email=?
            """,
            (email,)
        ).fetchone()


        connection.close()



        if user and check_password_hash(
            user["password"],
            password
        ):


            session["user_id"] = user["id"]


            return redirect(
                url_for("home")
            )


        flash(
            "Correo o contraseña incorrectos"
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





@app.route("/lesson/<int:id>")
def lesson(id):

    if not logged():

        return redirect(
            url_for("login")
        )


    selected = None


    for item in LESSONS:

        if item["id"] == id:

            selected = item
            break



    if not selected:

        return "Lección no encontrada",404



    return render_template(
        "lesson.html",
        lesson=selected,
        current_user=current_user()
    )






@app.route(
    "/activate-admin",
    methods=["POST"]
)
def activate_admin():


    if not logged():

        return redirect(
            url_for("login")
        )


    code = request.form.get(
        "code",
        ""
    )


    if code != ADMIN_CODE:

        flash(
            "Código incorrecto"
        )

        return redirect(
            url_for("home")
        )


    user = current_user()


    connection = db()


    connection.execute(
        """
        UPDATE users
        SET is_admin=1
        WHERE id=?
        """,
        (user["id"],)
    )


    connection.commit()

    connection.close()


    flash(
        "Administrador activado"
    )


    return redirect(
        url_for("admin")
    )
    @app.route("/admin")
def admin():

    if not logged():

        return redirect(
            url_for("login")
        )


    user = current_user()


    if not user or user["is_admin"] != 1:

        flash(
            "No tienes permisos"
        )

        return redirect(
            url_for("home")
        )


    connection = db()


    users = connection.execute(
        """
        SELECT *
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()


    connection.close()


    return render_template(
        "admin.html",
        users=users,
        current_user=user
    )





@app.route(
    "/ai"
)
def ai():

    if not logged():

        return redirect(
            url_for("login")
        )


    return render_template(
        "ai.html"
    )





@app.route(
    "/ai/chat",
    methods=["POST"]
)
def ai_chat():


    if not logged():

        return jsonify(
            {
                "error":"Debes iniciar sesión"
            }
        ),401



    if ai_client is None:

        return jsonify(
            {
                "error":
                "IA no configurada"
            }
        )



    data = request.get_json()


    question = data.get(
        "question",
        ""
    )


    if not question:

        return jsonify(
            {
                "error":
                "Escribe una pregunta"
            }
        )



    try:

        response = ai_client.responses.create(

            model="gpt-5.6-luna",

            instructions="""

Eres Academy AI.

Ayudas con:

- Roblox Studio
- Luau
- programación
- creación de videojuegos

Responde en español.

Explica paso a paso para principiantes.

""",

            input=question

        )


        return jsonify(
            {
                "answer":
                response.output_text
            }
        )


    except Exception as error:

        print(error)


        return jsonify(
            {
                "error":
                "Error conectando con la IA"
            }
        )







@app.route(
    "/admin/console",
    methods=["POST"]
)
def admin_console():


    if not logged():

        return redirect(
            url_for("login")
        )


    user=current_user()


    if not user or user["is_admin"] != 1:

        return redirect(
            url_for("home")
        )



    command = request.form.get(
        "command",
        ""
    ).strip()



    connection=db()



    if command == "users":


        users=connection.execute(
            """
            SELECT email,is_admin
            FROM users
            """
        ).fetchall()



        for item in users:

            flash(
                item["email"]
            )



    elif command.startswith(
        "delete "
    ):


        email = command.replace(
            "delete ",
            ""
        )



        connection.execute(
            """
            DELETE FROM users
            WHERE email=?
            """,
            (email,)
        )


        flash(
            "Usuario eliminado"
        )



    else:

        flash(
            "Comando desconocido"
        )



    connection.commit()

    connection.close()


    return redirect(
        url_for("admin")
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
