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

from werkzeug.security import generate_password_hash, check_password_hash

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "academy-blox-secret-key-change-this"
)

DATABASE = "academy.db"

ADMIN_CODE = os.environ.get(
    "ADMIN_CODE",
    "BLOX-ADMIN-9382"
)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

AI_DAILY_LIMIT = 10


# ============================================================
# OPENAI
# ============================================================

ai_client = None

if OPENAI_API_KEY and OpenAI:
    try:
        ai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        ai_client = None


# ============================================================
# LECCIONES
# ============================================================

LESSONS = [
    {
        "id": 1,
        "title": "Introducción a Roblox Studio",
        "description": "Aprende qué es Roblox Studio y cómo comenzar a crear.",
        "content": """
Roblox Studio es la herramienta utilizada para crear experiencias
en Roblox.

Con Roblox Studio puedes crear mapas, juegos, sistemas,
interfaces, personajes y mucho más.

Antes de empezar a programar es importante conocer las partes
principales del programa:
- Explorer
- Properties
- Workspace
- ServerScriptService
- StarterGui
"""
    },
    {
        "id": 2,
        "title": "Tu primer Script",
        "description": "Aprende a crear tu primer script en Luau.",
        "content": """
Los scripts de Roblox utilizan Luau.

Un ejemplo sencillo es:

print("Hola Roblox")

Cuando ejecutes el juego, Roblox mostrará ese mensaje
en la ventana Output.

Los scripts pueden utilizarse para crear sistemas,
eventos, botones, movimientos y muchas otras funciones.
"""
    },
    {
        "id": 3,
        "title": "Variables en Luau",
        "description": "Aprende a guardar información utilizando variables.",
        "content": """
Una variable permite guardar información.

Ejemplo:

local nombre = "Jugador"
local monedas = 100

Después puedes utilizar esas variables dentro del script.

Por ejemplo:

print(nombre)
print(monedas)
"""
    },
    {
        "id": 4,
        "title": "Eventos",
        "description": "Aprende cómo funcionan los eventos.",
        "content": """
Los eventos permiten que un script reaccione cuando ocurre algo.

Por ejemplo, una pieza puede detectar cuando un jugador
la toca.

Ejemplo:

part.Touched:Connect(function(hit)
    print("La pieza fue tocada")
end)

Los eventos son fundamentales para crear juegos interactivos.
"""
    },
    {
        "id": 5,
        "title": "Funciones",
        "description": "Aprende a crear funciones en Luau.",
        "content": """
Una función es un bloque de código que puedes ejecutar
cuando lo necesites.

Ejemplo:

local function saludar()
    print("Hola jugador")
end

saludar()

Las funciones ayudan a organizar los scripts y evitar
repetir código.
"""
    }
]


# ============================================================
# BASE DE DATOS
# ============================================================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            is_blocked INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS ai_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            usage_date TEXT NOT NULL,
            message_count INTEGER NOT NULL DEFAULT 0,
            UNIQUE(user_id, usage_date),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


init_db()


# ============================================================
# FUNCIONES DE USUARIO
# ============================================================

def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    connection = get_db()

    user = connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    connection.close()

    return user


def login_required():
    return "user_id" in session


# ============================================================
# FUNCIONES DE IA
# ============================================================

def get_ai_usage(user_id):
    today = date.today().isoformat()

    connection = get_db()

    row = connection.execute(
        """
        SELECT message_count
        FROM ai_usage
        WHERE user_id = ?
        AND usage_date = ?
        """,
        (user_id, today)
    ).fetchone()

    connection.close()

    if row is None:
        return 0

    return row["message_count"]


def get_ai_remaining(user_id):
    used = get_ai_usage(user_id)

    remaining = AI_DAILY_LIMIT - used

    if remaining < 0:
        remaining = 0

    return remaining


def consume_ai_message(user_id):
    today = date.today().isoformat()

    connection = get_db()

    connection.execute(
        """
        INSERT INTO ai_usage (
            user_id,
            usage_date,
            message_count
        )
        VALUES (?, ?, 1)

        ON CONFLICT(user_id, usage_date)
        DO UPDATE SET
            message_count = message_count + 1
        """,
        (user_id, today)
    )

    connection.commit()
    connection.close()


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def index():

    if not login_required():
        return redirect(url_for("login"))

    return render_template(
        "index.html",
        lessons=LESSONS
    )


# ============================================================
# REGISTRO
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Completa todos los campos.")
            return redirect(url_for("register"))

        connection = get_db()

        existing = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing:
            connection.close()

            flash("Ese correo ya está registrado.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        connection.execute(
            """
            INSERT INTO users (
                email,
                password_hash,
                created_at
            )
            VALUES (?, ?, datetime('now'))
            """,
            (email, password_hash)
        )

        connection.commit()
        connection.close()

        flash("Cuenta creada correctamente.")
        return redirect(url_for("login"))

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_db()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        connection.close()

        if not user:
            flash("Correo o contraseña incorrectos.")
            return redirect(url_for("login"))

        if user["is_blocked"]:
            flash("Esta cuenta está bloqueada.")
            return redirect(url_for("login"))

        if not check_password_hash(
            user["password_hash"],
            password
        ):
            flash("Correo o contraseña incorrectos.")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]

        return redirect(url_for("index"))

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# LECCIONES
# ============================================================

@app.route("/lesson/<int:lesson_id>")
def lesson(lesson_id):

    if not login_required():
        return redirect(url_for("login"))

    selected_lesson = None

    for item in LESSONS:
        if item["id"] == lesson_id:
            selected_lesson = item
            break

    if selected_lesson is None:
        return "Lección no encontrada", 404

    return render_template(
        "lesson.html",
        lesson=selected_lesson
    )


# ============================================================
# ACADEMY AI
# ============================================================

@app.route("/ai")
def ai_page():

    if not login_required():
        return redirect(url_for("login"))

    user = get_current_user()

    if not user:
        session.clear()
        return redirect(url_for("login"))

    remaining = get_ai_remaining(user["id"])

    return render_template(
        "ai.html",
        remaining=remaining,
        daily_limit=AI_DAILY_LIMIT
    )


# ============================================================
# CHAT DE ACADEMY AI
# ============================================================

@app.route("/ai/chat", methods=["POST"])
def academy_ai():

    if not login_required():
        return jsonify({
            "success": False,
            "error": "Debes iniciar sesión."
        }), 401

    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "error": "Sesión no válida."
        }), 401

    # --------------------------------------------------------
    # Comprobar límite
    # --------------------------------------------------------

    remaining = get_ai_remaining(user["id"])

    if remaining <= 0:
        return jsonify({
            "success": False,
            "error": "Has alcanzado tu límite de 10 preguntas de hoy.",
            "remaining": 0
        }), 429

    # --------------------------------------------------------
    # Comprobar API
    # --------------------------------------------------------

    if ai_client is None:
        return jsonify({
            "success": False,
            "error": "La IA todavía no está configurada. Comprueba OPENAI_API_KEY en Render."
        }), 503

    # --------------------------------------------------------
    # Obtener pregunta
    # --------------------------------------------------------

    data = request.get_json(silent=True) or {}

    question = str(
        data.get("question", "")
    ).strip()

    if not question:
        return jsonify({
            "success": False,
            "error": "Escribe una pregunta."
        }), 400

    if len(question) > 4000:
        return jsonify({
            "success": False,
            "error": "La pregunta es demasiado larga. Máximo 4000 caracteres."
        }), 400

    # --------------------------------------------------------
    # Instrucciones de Academy AI
    # --------------------------------------------------------

    instructions = """
Eres Academy AI, el asistente educativo de Academy Blox Script.

Tu especialidad es enseñar:
- Roblox Studio
- Luau
- programación
- creación de videojuegos
- scripts
- interfaces
- sistemas de Roblox

Responde en español.

Explica las cosas de forma sencilla y paso a paso.

Si el usuario pide código:
- entrega código completo cuando sea necesario;
- usa Luau correcto;
- explica dónde colocar el script;
- indica si debe utilizar Script, LocalScript o ModuleScript;
- explica qué debe hacer después de pegarlo.

Si el usuario es principiante, evita asumir conocimientos avanzados.

No inventes funciones de Roblox.

Si existe un error en el código del usuario, explica cuál es el problema
y proporciona una versión corregida.

Mantén las respuestas útiles y relativamente concisas.
"""

    # --------------------------------------------------------
    # Consumir mensaje
    # --------------------------------------------------------

    consume_ai_message(user["id"])

    # --------------------------------------------------------
    # Llamar a OpenAI
    # --------------------------------------------------------

    try:

        response = ai_client.responses.create(
            model="gpt-5.6-luna",
            instructions=instructions,
            input=question
        )

        answer = response.output_text

        if not answer:
            answer = "La IA no devolvió una respuesta."

        new_remaining = get_ai_remaining(user["id"])

        return jsonify({
            "success": True,
            "answer": answer,
            "remaining": new_remaining
        })

    except Exception as error:

        print("ERROR OPENAI:", repr(error))

        return jsonify({
            "success": False,
            "error": "No se pudo conectar con la IA. Revisa la API key y los logs de Render."
        }), 500


# ============================================================
# ADMIN
# ============================================================

@app.route("/admin")
def admin():

    if not login_required():
        return redirect(url_for("login"))

    user = get_current_user()

    if not user or not user["is_admin"]:
        flash("No tienes permisos de administrador.")
        return redirect(url_for("index"))

    connection = get_db()

    users = connection.execute(
        """
        SELECT
            id,
            email,
            is_admin,
            is_blocked,
            created_at
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin.html",
        users=users
    )


# ============================================================
# ACTIVAR ADMIN
# ============================================================

@app.route("/activate-admin", methods=["POST"])
def activate_admin():

    if not login_required():
        return redirect(url_for("login"))

    code = request.form.get("code", "").strip()

    if code != ADMIN_CODE:
        flash("Código de administrador incorrecto.")
        return redirect(url_for("index"))

    user = get_current_user()

    if not user:
        return redirect(url_for("login"))

    connection = get_db()

    connection.execute(
        """
        UPDATE users
        SET is_admin = 1
        WHERE id = ?
        """,
        (user["id"],)
    )

    connection.commit()
    connection.close()

    flash("Cuenta convertida en administrador.")

    return redirect(url_for("admin"))


# ============================================================
# CONSOLA ADMIN
# ============================================================

@app.route("/admin/console", methods=["POST"])
def admin_console():

    if not login_required():
        return redirect(url_for("login"))

    user = get_current_user()

    if not user or not user["is_admin"]:
        flash("No tienes permisos.")
        return redirect(url_for("index"))

    command = request.form.get(
        "command",
        ""
    ).strip()

    if not command:
        flash("Escribe un comando.")
        return redirect(url_for("admin"))

    parts = command.split()

    action = parts[0].lower()

    connection = get_db()

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if action == "help":

        flash(
            "Comandos: users | stats | block email | unblock email | "
            "makeadmin email | removeadmin email | delete email"
        )

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    elif action == "users":

        users = connection.execute(
            """
            SELECT email, is_admin, is_blocked
            FROM users
            ORDER BY id DESC
            """
        ).fetchall()

        for u in users:

            status = []

            if u["is_admin"]:
                status.append("ADMIN")

            if u["is_blocked"]:
                status.append("BLOQUEADO")

            label = ", ".join(status) if status else "USUARIO"

            flash(
                f'{u["email"]} - {label}'
            )

    # --------------------------------------------------------
    # STATS
    # --------------------------------------------------------

    elif action == "stats":

        total_users = connection.execute(
            "SELECT COUNT(*) AS total FROM users"
        ).fetchone()["total"]

        total_admins = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM users
            WHERE is_admin = 1
            """
        ).fetchone()["total"]

        blocked = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM users
            WHERE is_blocked = 1
            """
        ).fetchone()["total"]

        flash(
            f"Usuarios: {total_users} | "
            f"Admins: {total_admins} | "
            f"Bloqueados: {blocked}"
        )

    # --------------------------------------------------------
    # BLOCK
    # --------------------------------------------------------

    elif action == "block" and len(parts) >= 2:

        email = parts[1].lower()

        connection.execute(
            """
            UPDATE users
            SET is_blocked = 1
            WHERE email = ?
            """,
            (email,)
        )

        flash(f"Usuario bloqueado: {email}")

    # --------------------------------------------------------
    # UNBLOCK
    # --------------------------------------------------------

    elif action == "unblock" and len(parts) >= 2:

        email = parts[1].lower()

        connection.execute(
            """
            UPDATE users
            SET is_blocked = 0
            WHERE email = ?
            """,
            (email,)
        )

        flash(f"Usuario desbloqueado: {email}")

    # --------------------------------------------------------
    # MAKE ADMIN
    # --------------------------------------------------------

    elif action == "makeadmin" and len(parts) >= 2:

        email = parts[1].lower()

        connection.execute(
            """
            UPDATE users
            SET is_admin = 1
            WHERE email = ?
            """,
            (email,)
        )

        flash(f"Administrador creado: {email}")

    # --------------------------------------------------------
    # REMOVE ADMIN
    # --------------------------------------------------------

    elif action == "removeadmin" and len(parts) >= 2:

        email = parts[1].lower()

        connection.execute(
            """
            UPDATE users
            SET is_admin = 0
            WHERE email = ?
            """,
            (email,)
        )

        flash(f"Administrador eliminado: {email}")

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    elif action == "delete" and len(parts) >= 2:

        email = parts[1].lower()

        target = connection.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if target:

            connection.execute(
                """
                DELETE FROM ai_usage
                WHERE user_id = ?
                """,
                (target["id"],)
            )

            connection.execute(
                """
                DELETE FROM users
                WHERE id = ?
                """,
                (target["id"],)
            )

            flash(f"Usuario eliminado: {email}")

        else:

            flash("Usuario no encontrado.")

    else:

        flash("Comando desconocido. Usa: help")

    connection.commit()
    connection.close()

    return redirect(url_for("admin"))


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
