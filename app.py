import os
import sqlite3
from functools import wraps

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


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "academy-blox-secret-key-change-this"
)

DATABASE = "academy.db"

ADMIN_CODE = os.environ.get(
    "ADMIN_CODE",
    "ACADEMY-2026"
)


# =========================================================
# BASE DE DATOS
# =========================================================

def get_db():

    db = sqlite3.connect(DATABASE)

    db.row_factory = sqlite3.Row

    return db


def column_exists(db, table, column):

    columns = db.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return any(
        row["name"] == column
        for row in columns
    )


def init_db():

    db = get_db()


    # -----------------------------------------------------
    # USUARIOS
    # -----------------------------------------------------

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # Actualizar bases antiguas

    if not column_exists(db, "users", "is_admin"):

        db.execute(
            "ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0"
        )


    if not column_exists(db, "users", "is_blocked"):

        db.execute(
            "ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0"
        )


    if not column_exists(db, "users", "created_at"):

        db.execute(
            "ALTER TABLE users ADD COLUMN created_at TIMESTAMP"
        )


    # -----------------------------------------------------
    # LECCIONES
    # -----------------------------------------------------

    db.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            content TEXT,
            category TEXT DEFAULT 'Roblox Studio',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    if not column_exists(db, "lessons", "category"):

        db.execute(
            """
            ALTER TABLE lessons
            ADD COLUMN category TEXT DEFAULT 'Roblox Studio'
            """
        )


    # -----------------------------------------------------
    # SCRIPTS
    # -----------------------------------------------------

    db.execute("""
        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            code TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # -----------------------------------------------------

    db.commit()

    db.close()


# =========================================================
# FUNCIONES DE USUARIO
# =========================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("user_id"):

            flash(
                "Debes iniciar sesión para continuar."
            )

            return redirect(
                url_for("login")
            )


        db = get_db()

        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],)
        ).fetchone()

        db.close()


        if not user:

            session.clear()

            flash(
                "Tu sesión ya no es válida."
            )

            return redirect(
                url_for("login")
            )


        if user["is_blocked"]:

            session.clear()

            flash(
                "Tu cuenta está bloqueada."
            )

            return redirect(
                url_for("login")
            )


        return function(*args, **kwargs)


    return wrapper


def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("user_id"):

            flash(
                "Debes iniciar sesión."
            )

            return redirect(
                url_for("login")
            )


        if not session.get("is_admin"):

            flash(
                "No tienes permisos de administrador."
            )

            return redirect(
                url_for("index")
            )


        return function(*args, **kwargs)


    return wrapper


# =========================================================
# INICIO
# =========================================================

@app.route("/")
def index():

    db = get_db()


    scripts = db.execute(
        """
        SELECT *
        FROM scripts
        ORDER BY id DESC
        LIMIT 6
        """
    ).fetchall()


    lessons = db.execute(
        """
        SELECT *
        FROM lessons
        ORDER BY id ASC
        LIMIT 6
        """
    ).fetchall()


    db.close()


    return render_template(
        "index.html",
        scripts=scripts,
        lessons=lessons
    )


# =========================================================
# REGISTRO
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()


        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        password = request.form.get(
            "password",
            ""
        )


        if len(username) < 3:

            flash(
                "El usuario debe tener al menos 3 caracteres."
            )

            return render_template(
                "register.html"
            )


        if len(password) < 6:

            flash(
                "La contraseña debe tener al menos 6 caracteres."
            )

            return render_template(
                "register.html"
            )


        db = get_db()


        existing = db.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
               OR email = ?
            """,
            (
                username,
                email
            )
        ).fetchone()


        if existing:

            db.close()

            flash(
                "El usuario o correo ya está registrado."
            )

            return render_template(
                "register.html"
            )


        password_hash = generate_password_hash(
            password
        )


        db.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password,
                is_admin,
                is_blocked
            )
            VALUES (?, ?, ?, 0, 0)
            """,
            (
                username,
                email,
                password_hash
            )
        )


        db.commit()

        db.close()


        flash(
            "Cuenta creada correctamente. Ya puedes iniciar sesión."
        )


        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()


        password = request.form.get(
            "password",
            ""
        )


        db = get_db()


        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
               OR email = ?
            """,
            (
                username,
                username.lower()
            )
        ).fetchone()


        db.close()


        if not user:

            flash(
                "Usuario, correo o contraseña incorrectos."
            )

            return render_template(
                "login.html"
            )


        if user["is_blocked"]:

            flash(
                "Esta cuenta está bloqueada."
            )

            return render_template(
                "login.html"
            )


        if not check_password_hash(
            user["password"],
            password
        ):

            flash(
                "Usuario, correo o contraseña incorrectos."
            )

            return render_template(
                "login.html"
            )


        session.clear()


        session["user_id"] = user["id"]

        session["username"] = user["username"]

        session["email"] = user["email"]

        session["is_admin"] = bool(
            user["is_admin"]
        )


        return redirect(
            url_for("index")
        )


    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Sesión cerrada."
    )

    return redirect(
        url_for("index")
    )


# =========================================================
# CUENTA
# =========================================================

@app.route("/account")
@login_required
def account():

    db = get_db()


    user = db.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()


    db.close()


    return render_template(
        "index.html",
        scripts=[],
        lessons=[],
        account=user
    )


# =========================================================
# SCRIPTS
# =========================================================

@app.route("/scripts")
def scripts():

    search = request.args.get(
        "search",
        ""
    ).strip()


    category = request.args.get(
        "category",
        ""
    ).strip()


    db = get_db()


    query = """
        SELECT *
        FROM scripts
        WHERE 1 = 1
    """


    params = []


    if search:

        query += """
            AND (
                title LIKE ?
                OR description LIKE ?
                OR code LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value
        ])


    if category:

        query += """
            AND category = ?
        """

        params.append(category)


    query += """
        ORDER BY id DESC
    """


    scripts_list = db.execute(
        query,
        params
    ).fetchall()


    categories = db.execute(
        """
        SELECT DISTINCT category
        FROM scripts
        ORDER BY category
        """
    ).fetchall()


    db.close()


    return render_template(
        "scripts.html",
        scripts=scripts_list,
        categories=categories,
        search=search,
        selected_category=category
    )


# =========================================================
# SCRIPT INDIVIDUAL
# =========================================================

@app.route("/script/<int:id>")
@login_required
def script_detail(id):

    db = get_db()


    script = db.execute(
        """
        SELECT *
        FROM scripts
        WHERE id = ?
        """,
        (id,)
    ).fetchone()


    db.close()


    if not script:

        return "Script no encontrado.", 404


    return render_template(
        "scripts.html",
        scripts=[script],
        categories=[],
        search="",
        selected_category=""
    )


# =========================================================
# LECCIONES
# =========================================================

@app.route("/lesson/<int:id>")
@login_required
def lesson(id):

    db = get_db()


    lesson_data = db.execute(
        """
        SELECT *
        FROM lessons
        WHERE id = ?
        """,
        (id,)
    ).fetchone()


    db.close()


    if not lesson_data:

        return "Lección no encontrada.", 404


    return render_template(
        "lesson.html",
        lesson=lesson_data
    )


# =========================================================
# ACTIVAR ADMIN
# =========================================================

@app.route(
    "/admin-code",
    methods=["GET", "POST"]
)
@login_required
def admin_code():

    if session.get("is_admin"):

        return redirect(
            url_for("admin")
        )


    if request.method == "POST":

        code = request.form.get(
            "code",
            ""
        ).strip()


        if code != ADMIN_CODE:

            flash(
                "Código de administrador incorrecto."
            )

            return render_template(
                "admin_code.html"
            )


        db = get_db()


        db.execute(
            """
            UPDATE users
            SET is_admin = 1
            WHERE id = ?
            """,
            (session["user_id"],)
        )


        db.commit()

        db.close()


        session["is_admin"] = True


        flash(
            "Administrador activado correctamente."
        )


        return redirect(
            url_for("admin")
        )


    return render_template(
        "admin_code.html"
    )


# =========================================================
# ADMIN
# =========================================================

@app.route(
    "/admin",
    methods=["GET", "POST"]
)
@admin_required
def admin():

    db = get_db()


    if request.method == "POST":

        action = request.form.get(
            "action",
            ""
        )


        # -------------------------------------------------
        # CREAR LECCIÓN
        # -------------------------------------------------

        if action == "create_lesson":

            title = request.form.get(
                "title",
                ""
            ).strip()


            description = request.form.get(
                "description",
                ""
            ).strip()


            content = request.form.get(
                "content",
                ""
            ).strip()


            category = request.form.get(
                "category",
                "Roblox Studio"
            ).strip()


            if title:

                db.execute(
                    """
                    INSERT INTO lessons
                    (
                        title,
                        description,
                        content,
                        category
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        title,
                        description,
                        content,
                        category
                    )
                )


                db.commit()


                flash(
                    "Lección creada correctamente."
                )


        # -------------------------------------------------
        # CREAR SCRIPT
        # -------------------------------------------------

        elif action == "create_script":

            title = request.form.get(
                "script_title",
                ""
            ).strip()


            description = request.form.get(
                "script_description",
                ""
            ).strip()


            code = request.form.get(
                "code",
                ""
            )


            category = request.form.get(
                "script_category",
                "General"
            ).strip()


            if title and code:

                db.execute(
                    """
                    INSERT INTO scripts
                    (
                        title,
                        description,
                        code,
                        category
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        title,
                        description,
                        code,
                        category
                    )
                )


                db.commit()


                flash(
                    "Script añadido correctamente."
                )


        # -------------------------------------------------
        # BLOQUEAR / DESBLOQUEAR
        # -------------------------------------------------

        elif action == "toggle_user":

            user_id = request.form.get(
                "user_id"
            )


            if user_id:

                db.execute(
                    """
                    UPDATE users
                    SET is_blocked =
                        CASE
                            WHEN is_blocked = 1
                            THEN 0
                            ELSE 1
                        END
                    WHERE id = ?
                    AND id != ?
                    """,
                    (
                        user_id,
                        session["user_id"]
                    )
                )


                db.commit()


                flash(
                    "Estado de la cuenta actualizado."
                )


    lessons = db.execute(
        """
        SELECT *
        FROM lessons
        ORDER BY id DESC
        """
    ).fetchall()


    scripts_list = db.execute(
        """
        SELECT *
        FROM scripts
        ORDER BY id DESC
        """
    ).fetchall()


    users = db.execute(
        """
        SELECT id, username, email, is_admin,
               is_blocked, created_at
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()


    db.close()


    return render_template(
        "admin.html",
        lessons=lessons,
        scripts=scripts_list,
        users=users
    )


# =========================================================
# ACADEMY AI
# =========================================================

@app.route(
    "/ai",
    methods=["GET", "POST"]
)
@login_required
def ai():

    response = None

    question = ""


    if request.method == "POST":

        question = request.form.get(
            "message",
            ""
        ).strip()


        if question:

            # Respuestas básicas mientras no se
            # conecte una API externa.

            lower = question.lower()


            if "roblox studio" in lower:

                response = (
                    "Roblox Studio es el programa utilizado "
                    "para crear experiencias de Roblox. "
                    "Puedes programar con Luau, construir "
                    "mapas y crear sistemas para tu juego."
                )


            elif "script" in lower:

                response = (
                    "Los scripts de Roblox se programan "
                    "principalmente con Luau. "
                    "Un Script normalmente se utiliza para "
                    "la lógica del servidor y un LocalScript "
                    "para lógica que necesita ejecutarse "
                    "en el cliente."
                )


            elif "lua" in lower or "luau" in lower:

                response = (
                    "Luau es el lenguaje basado en Lua "
                    "que utiliza Roblox. Puedes empezar "
                    "aprendiendo variables, funciones, "
                    "condicionales, bucles y eventos."
                )


            else:

                response = (
                    "Academy AI recibió tu pregunta. "
                    "Para preguntas específicas de Roblox, "
                    "incluye el código o explica qué quieres "
                    "que haga el script."
                )


    return render_template(
        "ai.html",
        response=response,
        question=question
    )


# =========================================================
# API PARA COMPROBAR SESIÓN
# =========================================================

@app.route("/api/session")
def api_session():

    return jsonify({
        "logged_in": bool(
            session.get("user_id")
        ),
        "username": session.get("username"),
        "email": session.get("email"),
        "is_admin": bool(
            session.get("is_admin")
        )
    })


# =========================================================
# INICIAR
# =========================================================

init_db()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
