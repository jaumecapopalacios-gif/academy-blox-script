import os
import secrets
import sqlite3
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    abort,
    flash,
    g
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32)
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

DATABASE = "academy.db"

ADMIN_CODE = os.environ.get(
    "ADMIN_CODE",
    "BLOX-ADMIN-9382"
)

LESSONS = [
    (
        "Lección 1: Introducción a Roblox Studio",
        "Aprende qué es Roblox Studio y cómo se organiza un proyecto.",
        "Practica creando una experiencia y reconoce Workspace, Explorer y Properties."
    ),
    (
        "Lección 2: Variables y tipos de datos",
        "Aprende a guardar información utilizando variables.",
        "Practica creando variables para nombre, monedas y nivel."
    ),
    (
        "Lección 3: Condicionales",
        "Aprende a utilizar if, elseif y else para tomar decisiones.",
        "Crea una condición que muestre diferentes mensajes según el nivel."
    ),
    (
        "Lección 4: Funciones",
        "Aprende a crear funciones para reutilizar código.",
        "Crea una función que calcule una recompensa."
    ),
    (
        "Lección 5: Eventos",
        "Aprende cómo los eventos permiten reaccionar a acciones.",
        "Haz que una pieza reaccione cuando un jugador la toque."
    ),
    (
        "Lección 6: Cliente, servidor y seguridad",
        "Aprende la diferencia entre cliente y servidor.",
        "Aprende por qué el servidor debe validar las acciones importantes."
    ),
    (
        "Lección 7: Crear un sistema completo",
        "Combina variables, funciones, condiciones y eventos.",
        "Crea una pequeña misión con una recompensa."
    )
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            is_blocked INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    columns = db.execute(
        "PRAGMA table_info(users)"
    ).fetchall()

    names = [column[1] for column in columns]

    if "is_blocked" not in names:
        db.execute("""
            ALTER TABLE users
            ADD COLUMN is_blocked INTEGER NOT NULL DEFAULT 0
        """)

    db.commit()
    db.close()


def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    db = get_db()

    return db.execute(
        """
        SELECT id, email, is_admin, is_blocked, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()


@app.context_processor
def inject_user():
    return {
        "current_user": get_current_user()
    }


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        user = get_current_user()

        if not user:
            return redirect(url_for("login"))

        if user["is_blocked"]:
            session.clear()
            flash("Tu cuenta está bloqueada.")
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        user = get_current_user()

        if not user:
            return redirect(url_for("login"))

        if user["is_blocked"]:
            session.clear()
            return redirect(url_for("login"))

        if not user["is_admin"]:
            abort(403)

        return function(*args, **kwargs)

    return wrapper


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )
    return response


@app.route("/")
@login_required
def index():
    return render_template(
        "index.html",
        lessons=LESSONS
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        admin_code = request.form.get("admin_code", "").strip()

        if not email or not password:
            flash("Completa todos los campos obligatorios.")
            return render_template("register.html")

        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.")
            return render_template("register.html")

        db = get_db()

        existing_user = db.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if existing_user:
            flash("Ese correo ya tiene una cuenta.")
            return render_template("register.html")

        correct_admin_code = secrets.compare_digest(
            admin_code,
            ADMIN_CODE
        )

        password_hash = generate_password_hash(password)

        db.execute(
            """
            INSERT INTO users (
                email,
                password_hash,
                is_admin,
                is_blocked
            )
            VALUES (?, ?, ?, 0)
            """,
            (
                email,
                password_hash,
                1 if correct_admin_code else 0
            )
        )

        db.commit()

        flash("Cuenta creada correctamente. Ahora inicia sesión.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()

        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if not user:
            flash("Correo o contraseña incorrectos.")
            return render_template("login.html")

        if user["is_blocked"]:
            flash("Esta cuenta está bloqueada.")
            return render_template("login.html")

        if not check_password_hash(
            user["password_hash"],
            password
        ):
            flash("Correo o contraseña incorrectos.")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]

        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/activate-admin", methods=["POST"])
@login_required
def activate_admin():
    code = request.form.get("admin_code", "").strip()

    if not secrets.compare_digest(code, ADMIN_CODE):
        flash("Código de administrador incorrecto.")
        return redirect(url_for("index"))

    db = get_db()
    user = get_current_user()

    db.execute(
        """
        UPDATE users
        SET is_admin = 1
        WHERE id = ?
        """,
        (user["id"],)
    )

    db.commit()

    flash("Tu cuenta ahora es administradora.")
    return redirect(url_for("admin"))


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/lesson/<int:number>")
@login_required
def lesson(number):
    if number < 1 or number > len(LESSONS):
        abort(404)

    title, explanation, practice = LESSONS[number - 1]

    return render_template(
        "lesson.html",
        number=number,
        title=title,
        explanation=explanation,
        practice=practice,
        total=len(LESSONS)
    )


@app.route("/admin")
@admin_required
def admin():
    db = get_db()

    users = db.execute(
        """
        SELECT id, email, is_admin, is_blocked, created_at
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()

    total_users = db.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    total_admins = db.execute(
        "SELECT COUNT(*) FROM users WHERE is_admin = 1"
    ).fetchone()[0]

    total_students = db.execute(
        "SELECT COUNT(*) FROM users WHERE is_admin = 0"
    ).fetchone()[0]

    total_blocked = db.execute(
        "SELECT COUNT(*) FROM users WHERE is_blocked = 1"
    ).fetchone()[0]

    console_output = request.args.get("output", "")

    return render_template(
        "admin.html",
        users=users,
        total_users=total_users,
        total_admins=total_admins,
        total_students=total_students,
        total_blocked=total_blocked,
        console_output=console_output
    )


@app.route("/admin/user/<int:user_id>/toggle-block", methods=["POST"])
@admin_required
def toggle_block(user_id):
    current_user = get_current_user()

    if current_user["id"] == user_id:
        flash("No puedes bloquear tu propia cuenta.")
        return redirect(url_for("admin"))

    db = get_db()

    user = db.execute(
        """
        SELECT is_blocked
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if not user:
        abort(404)

    new_status = 0 if user["is_blocked"] else 1

    db.execute(
        """
        UPDATE users
        SET is_blocked = ?
        WHERE id = ?
        """,
        (new_status, user_id)
    )

    db.commit()

    return redirect(url_for("admin"))


@app.route("/admin/user/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def toggle_admin(user_id):
    current_user = get_current_user()

    if current_user["id"] == user_id:
        flash("No puedes cambiar tu propio rol.")
        return redirect(url_for("admin"))

    db = get_db()

    user = db.execute(
        """
        SELECT is_admin
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if not user:
        abort(404)

    new_status = 0 if user["is_admin"] else 1

    db.execute(
        """
        UPDATE users
        SET is_admin = ?
        WHERE id = ?
        """,
        (new_status, user_id)
    )

    db.commit()

    return redirect(url_for("admin"))


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    current_user = get_current_user()

    if current_user["id"] == user_id:
        flash("No puedes eliminar tu propia cuenta.")
        return redirect(url_for("admin"))

    db = get_db()

    user = db.execute(
        """
        SELECT id
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if not user:
        abort(404)

    db.execute(
        """
        DELETE FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    db.commit()

    return redirect(url_for("admin"))


@app.route("/admin/console", methods=["POST"])
@admin_required
def admin_console():
    command = request.form.get("command", "").strip()

    if not command:
        output = "Escribe un comando. Usa help."
        return redirect(url_for("admin", output=output))

    parts = command.split()
    action = parts[0].lower()
    db = get_db()

    if action == "help":
        output = """COMANDOS

help
users
stats
block correo@ejemplo.com
unblock correo@ejemplo.com
makeadmin correo@ejemplo.com
removeadmin correo@ejemplo.com
delete correo@ejemplo.com
"""

    elif action == "users":
        users = db.execute(
            """
            SELECT email, is_admin, is_blocked
            FROM users
            ORDER BY id DESC
            """
        ).fetchall()

        if not users:
            output = "No hay usuarios registrados."
        else:
            lines = ["USUARIOS:"]

            for user in users:
                role = "ADMIN" if user["is_admin"] else "ALUMNO"
                status = "BLOQUEADO" if user["is_blocked"] else "ACTIVO"

                lines.append(
                    f"- {user['email']} | {role} | {status}"
                )

            output = "\n".join(lines)

    elif action == "stats":
        total = db.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        admins = db.execute(
            "SELECT COUNT(*) FROM users WHERE is_admin = 1"
        ).fetchone()[0]

        students = db.execute(
            "SELECT COUNT(*) FROM users WHERE is_admin = 0"
        ).fetchone()[0]

        blocked = db.execute(
            "SELECT COUNT(*) FROM users WHERE is_blocked = 1"
        ).fetchone()[0]

        output = (
            "ESTADÍSTICAS\n\n"
            f"Usuarios: {total}\n"
            f"Administradores: {admins}\n"
            f"Alumnos: {students}\n"
            f"Bloqueados: {blocked}"
        )

    elif action == "block":
        if len(parts) != 2:
            output = "Uso: block correo@ejemplo.com"
        else:
            email = parts[1].lower()

            user = db.execute(
                "SELECT id FROM users WHERE email = ?",
                (email,)
            ).fetchone()

            if not user:
                output = "No existe esa cuenta."
            else:
                current_user = get_current_user()

                if user["id"] == current_user["id"]:
                    output = "No puedes bloquear tu propia cuenta."
                else:
                    db.execute(
                        """
                        UPDATE users
                        SET is_blocked = 1
                        WHERE id = ?
                        """,
                        (user["id"],)
                    )
                    db.commit()
                    output = f"Cuenta bloqueada: {email}"

    elif action == "unblock":
        if len(parts) != 2:
            output = "Uso: unblock correo@ejemplo.com"
        else:
            email = parts[1].lower()

            cursor = db.execute(
                """
                UPDATE users
                SET is_blocked = 0
                WHERE email = ?
                """,
                (email,)
            )

            db.commit()

            output = (
                f"Cuenta desbloqueada: {email}"
                if cursor.rowcount
                else "No existe esa cuenta."
            )

    elif action == "makeadmin":
        if len(parts) != 2:
            output = "Uso: makeadmin correo@ejemplo.com"
        else:
            email = parts[1].lower()

            cursor = db.execute(
                """
                UPDATE users
                SET is_admin = 1
                WHERE email = ?
                """,
                (email,)
            )

            db.commit()

            output = (
                f"Ahora es administrador: {email}"
                if cursor.rowcount
                else "No existe esa cuenta."
            )

    elif action == "removeadmin":
        if len(parts) != 2:
            output = "Uso: removeadmin correo@ejemplo.com"
        else:
            email = parts[1].lower()
            current_user = get_current_user()

            target = db.execute(
                """
                SELECT id
                FROM users
                WHERE email = ?
                """,
                (email,)
            ).fetchone()

            if not target:
                output = "No existe esa cuenta."

            elif target["id"] == current_user["id"]:
                output = "No puedes quitarte tu propio admin."

            else:
                db.execute(
                    """
                    UPDATE users
                    SET is_admin = 0
                    WHERE id = ?
                    """,
                    (target["id"],)
                )

                db.commit()

                output = f"Permisos admin eliminados: {email}"

    elif action == "delete":
        if len(parts) != 2:
            output = "Uso: delete correo@ejemplo.com"
        else:
            email = parts[1].lower()
            current_user = get_current_user()

            target = db.execute(
                """
                SELECT id
                FROM users
                WHERE email = ?
                """,
                (email,)
            ).fetchone()

            if not target:
                output = "No existe esa cuenta."

            elif target["id"] == current_user["id"]:
                output = "No puedes eliminar tu propia cuenta."

            else:
                db.execute(
                    "DELETE FROM users WHERE id = ?",
                    (target["id"],)
                )

                db.commit()

                output = f"Cuenta eliminada: {email}"

    else:
        output = (
            f"Comando desconocido: {action}\n"
            "Escribe help para ver los comandos."
        )

    return redirect(
        url_for(
            "admin",
            output=output
        )
    )


@app.errorhandler(403)
def forbidden(error):
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>403</title>
    </head>
    <body style="
        background:#05070d;
        color:white;
        font-family:Arial;
        text-align:center;
        padding:80px;
    ">
        <h1>403</h1>
        <p>No tienes permiso para entrar aquí.</p>
        <a href="/" style="color:#168cff;">Volver</a>
    </body>
    </html>
    """, 403


init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )