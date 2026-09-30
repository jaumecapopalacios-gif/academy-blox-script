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
        "title": "Introducción a Roblox Studio",
        "description": "Aprende a crear tus primeros juegos.",
        "content": """
Roblox Studio es el programa oficial
para crear experiencias en Roblox.

Puedes crear mapas, sistemas,
interfaces y juegos completos.
"""
    },


    {
        "title": "Primer Script Luau",
        "description": "Aprende tu primer código.",
        "content": """
Roblox utiliza Luau.

Ejemplo:

print("Hola Roblox")
"""
    },


    {
        "title": "Variables",
        "description": "Guarda información usando variables.",
        "content": """
Ejemplo:

local monedas = 100

print(monedas)
"""
    },


    {
        "title": "Eventos",
        "description": "Haz que tu juego reaccione.",
        "content": """
Ejemplo:

part.Touched:Connect(function()

print("Tocado")

end)
"""
    },


    {
        "title": "Funciones",
        "description": "Organiza tu código.",
        "content": """
Ejemplo:

local function hola()

print("Hola")

end

hola()
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

        admin INTEGER DEFAULT 0,

        blocked INTEGER DEFAULT 0,

        created TEXT

    )
    """)



    con.execute("""
    CREATE TABLE IF NOT EXISTS ai_usage(

        user_id INTEGER,

        day TEXT,

        amount INTEGER DEFAULT 0,

        UNIQUE(user_id,day)

    )
    """)


    con.commit()

    con.close()



init_db()



def current_user():

    uid = session.get(
        "user_id"
    )


    if not uid:
        return None


    con = db()


    user = con.execute(
        "SELECT * FROM users WHERE id=?",
        (uid,)
    ).fetchone()


    con.close()


    return user



def logged():

    return "user_id" in session
def ai_used(user_id):

    today = date.today().isoformat()

    con = db()

    row = con.execute(
        """
        SELECT amount 
        FROM ai_usage
        WHERE user_id=? AND day=?
        """,
        (user_id, today)
    ).fetchone()

    con.close()

    if row:
        return row["amount"]

    return 0



def use_ai(user_id):

    today = date.today().isoformat()

    con = db()

    con.execute(
        """
        INSERT INTO ai_usage
        (user_id, day, amount)

        VALUES (?, ?, 1)

        ON CONFLICT(user_id, day)

        DO UPDATE SET amount = amount + 1
        """,
        (user_id, today)
    )

    con.commit()

    con.close()



# =========================
# REGISTRO
# =========================

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
                "Completa todos los campos"
            )

            return redirect(
                url_for("register")
            )


        con = db()


        exists = con.execute(
            "SELECT id FROM users WHERE email=?",
            (email,)
        ).fetchone()


        if exists:

            con.close()

            flash(
                "El usuario ya existe"
            )

            return redirect(
                url_for("register")
            )


        con.execute(
            """
            INSERT INTO users
            (email,password,created)

            VALUES (?,?,?)
            """,
            (
                email,
                generate_password_hash(password),
                date.today().isoformat()
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



# =========================
# LOGIN
# =========================

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


        con = db()


        user = con.execute(
            """
            SELECT *
            FROM users
            WHERE email=?
            """,
            (email,)
        ).fetchone()


        con.close()



        if not user:

            flash(
                "Datos incorrectos"
            )

            return redirect(
                url_for("login")
            )



        if user["blocked"]:

            flash(
                "Cuenta bloqueada"
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
            url_for("home")
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



# =========================
# PAGINA PRINCIPAL
# =========================

@app.route("/")
def home():

    if not logged():

        return redirect(
            url_for("login")
        )


    return render_template(
        "index.html",
        user=current_user(),
        lessons=LESSONS
    )



@app.route(
    "/lesson/<int:number>"
)
def lesson(number):

    if not logged():

        return redirect(
            url_for("login")
        )


    if number < 1 or number > len(LESSONS):

        return "Lección no encontrada"


    return render_template(
        "lesson.html",
        lesson=LESSONS[number-1],
        number=number
    )
# =========================
# ACTIVAR ADMIN
# =========================

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


    con = db()


    con.execute(
        """
        UPDATE users
        SET admin=1
        WHERE id=?
        """,
        (user["id"],)
    )


    con.commit()

    con.close()


    flash(
        "Ahora eres administrador"
    )


    return redirect(
        url_for("admin")
    )



# =========================
# PANEL ADMIN
# =========================

@app.route("/admin")
def admin():

    if not logged():

        return redirect(
            url_for("login")
        )


    user = current_user()


    if not user["admin"]:

        flash(
            "No tienes permisos"
        )

        return redirect(
            url_for("home")
        )



    con = db()


    users = con.execute(
        """
        SELECT *
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()


    con.close()



    return render_template(
        "admin.html",
        users=users
    )



# =========================
# CONSOLA ADMIN
# =========================

@app.route(
    "/admin/console",
    methods=["POST"]
)
def admin_console():

    if not logged():

        return redirect(
            url_for("login")
        )


    user = current_user()


    if not user["admin"]:

        return redirect(
            url_for("home")
        )



    command = request.form.get(
        "command",
        ""
    ).strip()



    parts = command.split()


    if len(parts) == 0:

        flash(
            "Escribe un comando"
        )

        return redirect(
            url_for("admin")
        )



    action = parts[0].lower()



    con = db()



    # ver usuarios
    if action == "users":


        users = con.execute(
            """
            SELECT email,admin,blocked
            FROM users
            """
        ).fetchall()


        for u in users:

            estado = "ADMIN" if u["admin"] else "USER"

            if u["blocked"]:

                estado += " BLOQUEADO"


            flash(
                f"{u['email']} - {estado}"
            )



    # bloquear usuario
    elif action == "block" and len(parts)>1:


        email = parts[1]


        con.execute(
            """
            UPDATE users
            SET blocked=1
            WHERE email=?
            """,
            (email,)
        )


        flash(
            "Usuario bloqueado"
        )



    # desbloquear
    elif action == "unblock" and len(parts)>1:


        email = parts[1]


        con.execute(
            """
            UPDATE users
            SET blocked=0
            WHERE email=?
            """,
            (email,)
        )


        flash(
            "Usuario desbloqueado"
        )



    # convertir admin
    elif action == "makeadmin" and len(parts)>1:


        email = parts[1]


        con.execute(
            """
            UPDATE users
            SET admin=1
            WHERE email=?
            """,
            (email,)
        )


        flash(
            "Administrador añadido"
        )



    # eliminar usuario
    elif action == "delete" and len(parts)>1:


        email = parts[1]


        con.execute(
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
            "Comandos: users | block correo | unblock correo | makeadmin correo | delete correo"
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


    user = current_user()


    remaining = AI_LIMIT - ai_used(
        user["id"]
    )


    return render_template(
        "ai.html",
        remaining=max(remaining,0)
    )



@app.route(
    "/ai/chat",
    methods=["POST"]
)
def ai_chat():

    if not logged():

        return jsonify({
            "error":"No iniciado"
        }),401



    user = current_user()



    remaining = AI_LIMIT - ai_used(
        user["id"]
    )



    if remaining <= 0:

        return jsonify({

            "error":
            "Llegaste al límite diario de preguntas"

        }),429




    if ai_client is None:

        return jsonify({

            "error":
            "La IA no está configurada"

        }),500




    data = request.get_json()


    question = data.get(
        "question",
        ""
    ).strip()



    if not question:

        return jsonify({

            "error":
            "Escribe una pregunta"

        }),400




    use_ai(
        user["id"]
    )



    instructions = """

Eres Academy AI de Academy Blox Script.

Enseña:

- Roblox Studio
- Luau
- programación
- creación de videojuegos

Responde en español.

Explica desde cero.

Si das código indica:
- dónde ponerlo
- si es Script, LocalScript o ModuleScript

Ayuda a principiantes.

"""



    try:


        response = ai_client.responses.create(

            model="gpt-5.6-luna",

            instructions=instructions,

            input=question

        )


        answer = response.output_text



        return jsonify({

            "answer":answer,

            "remaining":
            AI_LIMIT - ai_used(user["id"])

        })



    except Exception as e:


        print(
            "ERROR IA:",
            e
        )


        return jsonify({

            "error":
            "Error conectando con la IA"

        }),500




# =========================
# INICIAR SERVIDOR
# =========================


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
