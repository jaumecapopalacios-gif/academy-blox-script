import os
import sqlite3
import secrets
from functools import wraps
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    g
)

from werkzeug.security import generate_password_hash, check_password_hash

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# =========================================================
# CONFIGURACIÓN
# =========================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "academy.db")

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    secrets.token_hex(32)
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
)


# =========================================================
# BASE DE DATOS
# =========================================================

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row

    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def migrate_users_table(db):
    """
    Convierte la tabla vieja:

        username
        email
        password_hash
        ...

    en la nueva:

        email
        password_hash
        ...

    Se conservan los usuarios, sus contraseñas,
    administradores, bloqueos e IDs.
    """

    columns = db.execute(
        "PRAGMA table_info(users)"
    ).fetchall()

    if not columns:
        return

    column_names = [column["name"] for column in columns]

    # Si ya no existe username, no hacemos nada.
    if "username" not in column_names:
        return

    db.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    db.execute("""
        INSERT INTO users_new (
            id,
            email,
            password_hash,
            is_admin,
            is_blocked,
            created_at
        )
        SELECT
            id,
            email,
            password_hash,
            is_admin,
            is_blocked,
            created_at
        FROM users
    """)

    db.execute("DROP TABLE users")

    db.execute("""
        ALTER TABLE users_new
        RENAME TO users
    """)

    db.commit()


def init_db():
    db = get_db()

    # -----------------------------------------------------
    # USUARIOS
    # -----------------------------------------------------

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    db.commit()

    # Migrar la versión antigua si todavía tiene username.
    migrate_users_table(db)

    # -----------------------------------------------------
    # LECCIONES
    # -----------------------------------------------------

    db.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            content TEXT NOT NULL,
            code TEXT DEFAULT '',
            category TEXT DEFAULT 'Roblox Studio',
            created_at TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # SCRIPTS
    # -----------------------------------------------------

    db.execute("""
        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            code TEXT NOT NULL,
            category TEXT DEFAULT 'Luau',
            created_at TEXT NOT NULL
        )
    """)

    db.commit()

    seed_lessons()
    seed_scripts()


# =========================================================
# LECCIONES
# =========================================================

def seed_lessons():
    db = get_db()

    count = db.execute(
        "SELECT COUNT(*) AS total FROM lessons"
    ).fetchone()["total"]

    if count >= 24:
        return

    lessons = [
        (
            "Introducción a Roblox Studio",
            "Conoce Roblox Studio y sus herramientas principales.",
            """
Roblox Studio es el programa que utilizamos para crear
experiencias en Roblox.

En esta lección aprenderás a reconocer el Explorer,
Properties, Workspace, Parts y las herramientas básicas.
""",
            "",
            "Roblox Studio"
        ),

        (
            "Crear tu primer proyecto",
            "Aprende a crear un proyecto nuevo desde cero.",
            """
Para comenzar un juego debes crear un proyecto nuevo.

Puedes utilizar una plantilla como Baseplate para comenzar
con un espacio vacío y construir tu experiencia.
""",
            "",
            "Roblox Studio"
        ),

        (
            "Parts y construcción",
            "Aprende a crear y modificar Parts.",
            """
Las Parts son uno de los elementos fundamentales de Roblox.

Puedes cambiar su posición, tamaño, orientación, material
y color desde las propiedades.
""",
            "",
            "Construcción"
        ),

        (
            "Materiales y colores",
            "Aprende a cambiar el aspecto de tus objetos.",
            """
Roblox permite utilizar diferentes materiales y colores.

Los materiales ayudan a que las construcciones tengan
una apariencia diferente.
""",
            "",
            "Construcción"
        ),

        (
            "Modelos y organización profesional",
            "Aprende a organizar correctamente tu proyecto.",
            """
Un proyecto bien organizado es mucho más fácil de editar.

Utiliza carpetas, modelos y nombres claros para mantener
el Explorer ordenado.
""",
            "",
            "Construcción"
        ),

        (
            "Terrain",
            "Aprende los conceptos básicos del Terrain Editor.",
            """
El Terrain Editor permite crear montañas, agua,
cuevas y diferentes tipos de terreno.

Es especialmente útil para mapas grandes.
""",
            "",
            "Roblox Studio"
        ),

        (
            "Luau desde cero",
            "Introducción al lenguaje de programación Luau.",
            """
Luau es el lenguaje utilizado para programar en Roblox.

Una variable puede guardar información:

local monedas = 10

Después podemos utilizar esa información en nuestros
sistemas.
""",
            "local monedas = 10\nprint(monedas)",
            "Luau"
        ),

        (
            "Scripts y LocalScripts",
            "Conoce los diferentes tipos de scripts.",
            """
Los Scripts y LocalScripts permiten ejecutar código.

Los Scripts normalmente funcionan desde el servidor,
mientras que los LocalScripts se utilizan para lógica
del cliente.
""",
            "",
            "Luau"
        ),

        (
            "Eventos",
            "Aprende a utilizar eventos en Roblox.",
            """
Los eventos permiten ejecutar código cuando sucede algo.

Por ejemplo, podemos detectar cuando un jugador toca
una Part.
""",
            """local part = script.Parent

part.Touched:Connect(function(hit)
    print("Algo tocó la parte")
end)""",
            "Luau"
        ),

        (
            "Condicionales",
            "Aprende a utilizar if, elseif y else.",
            """
Los condicionales permiten que un programa tome
decisiones dependiendo de una condición.
""",
            """local monedas = 100

if monedas >= 100 then
    print("Puedes comprar el objeto")
else
    print("No tienes suficientes monedas")
end""",
            "Luau"
        ),

        (
            "Bucles y funciones",
            "Aprende a repetir acciones y reutilizar código.",
            """
Los bucles permiten repetir instrucciones.

Las funciones permiten guardar instrucciones para
utilizarlas cuando sean necesarias.
""",
            """local function saludar()
    print("Hola jugador")
end

saludar()""",
            "Luau"
        ),

        (
            "Tablas y datos",
            "Aprende a almacenar varios datos utilizando tablas.",
            """
Las tablas permiten almacenar múltiples valores.

Son fundamentales para crear inventarios,
configuraciones y sistemas de datos.
""",
            """local jugadores = {
    "Player1",
    "Player2",
    "Player3"
}

print(jugadores[1])""",
            "Luau"
        ),

        (
            "Sistema de checkpoints",
            "Aprende cómo funcionan los checkpoints.",
            """
Un sistema de checkpoints permite guardar el progreso
de un jugador dentro de un mapa.
""",
            "",
            "Sistemas"
        ),

        (
            "Sistema de monedas",
            "Crea un sistema básico de monedas.",
            """
Las monedas pueden utilizarse como recompensa
para los jugadores.

Después pueden gastarse en tiendas y otros sistemas.
""",
            "",
            "Sistemas"
        ),

        (
            "Leaderstats",
            "Crea estadísticas visibles para los jugadores.",
            """
Leaderstats permite mostrar estadísticas como monedas,
puntos o victorias en la tabla de jugadores.
""",
            """game.Players.PlayerAdded:Connect(function(player)

    local leaderstats = Instance.new("Folder")
    leaderstats.Name = "leaderstats"
    leaderstats.Parent = player

    local coins = Instance.new("IntValue")
    coins.Name = "Coins"
    coins.Value = 0
    coins.Parent = leaderstats

end)""",
            "Sistemas"
        ),

        (
            "Interfaces GUI",
            "Aprende los fundamentos de las interfaces.",
            """
Las interfaces GUI permiten mostrar botones,
textos, imágenes y menús al jugador.
""",
            "",
            "GUI"
        ),

        (
            "Menús profesionales",
            "Aprende a crear menús más completos.",
            """
Un menú puede incluir botones para jugar,
configuración, tienda, inventario y otras funciones.
""",
            "",
            "GUI"
        ),

        (
            "Tiendas",
            "Aprende los fundamentos para crear una tienda.",
            """
Una tienda puede permitir que los jugadores gasten
sus monedas para comprar objetos.
""",
            "",
            "Sistemas"
        ),

        (
            "RemoteEvents",
            "Aprende a comunicar cliente y servidor.",
            """
RemoteEvents permiten enviar información entre
el cliente y el servidor.

Son importantes para construir sistemas
multijugador correctamente.
""",
            "",
            "Avanzado"
        ),

        (
            "DataStore",
            "Aprende los fundamentos de guardar datos.",
            """
DataStore permite guardar información de los jugadores
para que pueda recuperarse cuando vuelvan a entrar.
""",
            "",
            "Avanzado"
        ),

        (
            "Sistemas avanzados",
            "Combina diferentes sistemas de Roblox.",
            """
Los sistemas avanzados combinan programación,
interfaces, datos, eventos y otras herramientas.
""",
            "",
            "Avanzado"
        ),

        (
            "Seguridad y Anti-Exploit",
            "Aprende conceptos básicos de seguridad.",
            """
La lógica importante debe validarse en el servidor.

Nunca debes confiar completamente en los datos enviados
por el cliente.
""",
            "",
            "Seguridad"
        ),

        (
            "Optimización",
            "Aprende conceptos básicos para mejorar el rendimiento.",
            """
La optimización ayuda a que una experiencia funcione
mejor en diferentes dispositivos.

Debes evitar objetos y procesos innecesarios.
""",
            "",
            "Optimización"
        ),

        (
            "Crear y publicar un juego",
            "Aprende los pasos finales para publicar tu experiencia.",
            """
Cuando tu juego esté terminado puedes probarlo,
corregir errores y finalmente publicarlo desde
Roblox Studio.
""",
            "",
            "Roblox Studio"
        )
    ]

    existing = db.execute(
        "SELECT title FROM lessons"
    ).fetchall()

    existing_titles = {
        row["title"]
        for row in existing
    }

    now = datetime.utcnow().isoformat()

    for title, description, content, code, category in lessons:

        if title in existing_titles:
            continue

        db.execute("""
            INSERT INTO lessons (
                title,
                description,
                content,
                code,
                category,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            content,
            code,
            category,
            now
        ))

    db.commit()


# =========================================================
# SCRIPTS
# =========================================================

def seed_scripts():
    db = get_db()

    count = db.execute(
        "SELECT COUNT(*) AS total FROM scripts"
    ).fetchone()["total"]

    if count > 0:
        return

    scripts = [
        (
            "Sistema de Leaderstats",
            "Crea una estadística de monedas.",
            """game.Players.PlayerAdded:Connect(function(player)

    local leaderstats = Instance.new("Folder")
    leaderstats.Name = "leaderstats"
    leaderstats.Parent = player

    local coins = Instance.new("IntValue")
    coins.Name = "Coins"
    coins.Value = 0
    coins.Parent = leaderstats

end)""",
            "Luau"
        ),

        (
            "Puerta con ProximityPrompt",
            "Permite abrir una puerta acercándose a ella.",
            """local prompt = script.Parent.ProximityPrompt

prompt.Triggered:Connect(function(player)

    script.Parent.Transparency = 1
    script.Parent.CanCollide = false

end)""",
            "Luau"
        ),

        (
            "Parte que elimina al jugador",
            "Elimina al personaje cuando toca una pieza.",
            """local part = script.Parent

part.Touched:Connect(function(hit)

    local character = hit.Parent
    local humanoid = character:FindFirstChild("Humanoid")

    if humanoid then
        humanoid.Health = 0
    end

end)""",
            "Luau"
        ),

        (
            "Dar monedas al tocar una pieza",
            "Entrega monedas al jugador cuando toca una Part.",
            """local part = script.Parent

part.Touched:Connect(function(hit)

    local character = hit.Parent
    local player = game.Players:GetPlayerFromCharacter(character)

    if player then

        local leaderstats = player:FindFirstChild("leaderstats")

        if leaderstats then

            local coins = leaderstats:FindFirstChild("Coins")

            if coins then
                coins.Value += 10
            end

        end

    end

end)""",
            "Luau"
        ),

        (
            "Botón GUI",
            "Ejemplo básico de un botón de interfaz.",
            """local button = script.Parent

button.MouseButton1Click:Connect(function()

    print("Botón presionado")

end)""",
            "GUI"
        ),

        (
            "Mensaje al entrar",
            "Muestra un mensaje cuando entra un jugador.",
            """game.Players.PlayerAdded:Connect(function(player)

    print("Bienvenido " .. player.Name)

end)""",
            "Luau"
        )
    ]

    now = datetime.utcnow().isoformat()

    for title, description, code, category in scripts:

        db.execute("""
            INSERT INTO scripts (
                title,
                description,
                code,
                category,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            description,
            code,
            category,
            now
        ))

    db.commit()


# =========================================================
# USUARIO ACTUAL
# =========================================================

@app.before_request
def load_user():

    g.user = None

    user_id = session.get("user_id")

    if not user_id:
        return

    db = get_db()

    user = db.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if user is None:
        session.clear()
        return

    if user["is_blocked"]:
        session.clear()
        flash("Tu cuenta está bloqueada.", "error")
        return redirect(url_for("login"))

    g.user = user


@app.context_processor
def inject_user():

    return {
        "user": g.user,
        "logged_in": g.user is not None
    }


# =========================================================
# DECORADORES
# =========================================================

def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if g.user is None:
            flash(
                "Debes iniciar sesión para continuar.",
                "error"
            )
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if g.user is None:
            flash(
                "Debes iniciar sesión.",
                "error"
            )
            return redirect(url_for("login"))

        if not g.user["is_admin"]:
            flash(
                "No tienes permisos de administrador.",
                "error"
            )
            return redirect(url_for("index"))

        return view(*args, **kwargs)

    return wrapped_view


# =========================================================
# INICIO
# =========================================================

@app.route("/")
def index():

    db = get_db()

    lessons = db.execute("""
        SELECT *
        FROM lessons
        ORDER BY id DESC
        LIMIT 6
    """).fetchall()

    scripts = db.execute("""
        SELECT *
        FROM scripts
        ORDER BY id DESC
        LIMIT 6
    """).fetchall()

    return render_template(
        "index.html",
        lessons=lessons,
        scripts=scripts
    )


# =========================================================
# REGISTRO
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if g.user is not None:
        return redirect(url_for("index"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email:
            flash(
                "Introduce tu correo electrónico.",
                "error"
            )
            return render_template("register.html")

        if len(password) < 6:
            flash(
                "La contraseña debe tener al menos 6 caracteres.",
                "error"
            )
            return render_template("register.html")

        db = get_db()

        exists = db.execute("""
            SELECT id
            FROM users
            WHERE lower(email) = ?
        """, (email,)).fetchone()

        if exists:
            flash(
                "Ese correo ya está registrado.",
                "error"
            )
            return render_template("register.html")

        password_hash = generate_password_hash(
            password
        )

        now = datetime.utcnow().isoformat()

        db.execute("""
            INSERT INTO users (
                email,
                password_hash,
                is_admin,
                is_blocked,
                created_at
            )
            VALUES (?, ?, 0, 0, ?)
        """, (
            email,
            password_hash,
            now
        ))

        db.commit()

        flash(
            "Cuenta creada correctamente. Ahora inicia sesión.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if g.user is not None:
        return redirect(url_for("index"))

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
                "Introduce tu correo y contraseña.",
                "error"
            )
            return render_template("login.html")

        db = get_db()

        user = db.execute("""
            SELECT *
            FROM users
            WHERE lower(email) = ?
        """, (email,)).fetchone()

        if user is None:
            flash(
                "Correo o contraseña incorrecta.",
                "error"
            )
            return render_template("login.html")

        if user["is_blocked"]:
            flash(
                "Esta cuenta está bloqueada.",
                "error"
            )
            return render_template("login.html")

        if not check_password_hash(
            user["password_hash"],
            password
        ):
            flash(
                "Correo o contraseña incorrecta.",
                "error"
            )
            return render_template("login.html")

        session.clear()

        session["user_id"] = user["id"]
        session["email"] = user["email"]
        session["is_admin"] = bool(user["is_admin"])

        flash(
            "Has iniciado sesión correctamente.",
            "success"
        )

        return redirect(url_for("index"))

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Sesión cerrada.",
        "success"
    )

    return redirect(url_for("index"))


# =========================================================
# LECCIONES
# =========================================================

@app.route("/lessons")
def lessons():

    db = get_db()

    lessons_list = db.execute("""
        SELECT *
        FROM lessons
        ORDER BY id ASC
    """).fetchall()

    return render_template(
        "lessons.html",
        lessons=lessons_list
    )


@app.route("/lesson/<int:lesson_id>")
def lesson_detail(lesson_id):

    db = get_db()

    lesson = db.execute("""
        SELECT *
        FROM lessons
        WHERE id = ?
    """, (lesson_id,)).fetchone()

    if lesson is None:
        flash(
            "La lección no existe.",
            "error"
        )
        return redirect(url_for("lessons"))

    return render_template(
        "lesson.html",
        lesson=lesson
    )


# =========================================================
# SCRIPTS
# =========================================================

@app.route("/scripts")
def scripts():

    db = get_db()

    q = request.args.get(
        "q",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()

    sql = """
        SELECT *
        FROM scripts
        WHERE 1 = 1
    """

    params = []

    if q:

        sql += """
            AND (
                title LIKE ?
                OR description LIKE ?
                OR code LIKE ?
            )
        """

        search = f"%{q}%"

        params.extend([
            search,
            search,
            search
        ])

    if category:

        sql += """
            AND category = ?
        """

        params.append(category)

    sql += """
        ORDER BY id DESC
    """

    scripts_list = db.execute(
        sql,
        params
    ).fetchall()

    categories = db.execute("""
        SELECT DISTINCT category
        FROM scripts
        ORDER BY category
    """).fetchall()

    return render_template(
        "scripts.html",
        scripts=scripts_list,
        categories=categories,
        q=q,
        category=category
    )


# =========================================================
# ACTIVAR ADMIN
# =========================================================

@app.route(
    "/activate-admin",
    methods=["GET", "POST"]
)
@login_required
def activate_admin():

    if request.method == "POST":

        code = request.form.get(
            "code",
            ""
        ).strip()

        admin_code = os.getenv(
            "ADMIN_CODE",
            "CAMBIA-ESTE-CODIGO"
        )

        if not secrets.compare_digest(
            code,
            admin_code
        ):
            flash(
                "Código de administrador incorrecto.",
                "error"
            )
            return redirect(
                url_for("activate_admin")
            )

        db = get_db()

        db.execute("""
            UPDATE users
            SET is_admin = 1
            WHERE id = ?
        """, (
            g.user["id"],
        ))

        db.commit()

        session["is_admin"] = True

        flash(
            "Administrador activado correctamente.",
            "success"
        )

        return redirect(url_for("admin"))

    return render_template(
        "activate_admin.html"
    )


# =========================================================
# PANEL ADMIN
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

            code = request.form.get(
                "code",
                ""
            )

            category = request.form.get(
                "category",
                "Roblox Studio"
            ).strip()

            if not title or not description or not content:

                flash(
                    "Completa los campos obligatorios.",
                    "error"
                )

                return redirect(
                    url_for("admin")
                )

            db.execute("""
                INSERT INTO lessons (
                    title,
                    description,
                    content,
                    code,
                    category,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                title,
                description,
                content,
                code,
                category,
                datetime.utcnow().isoformat()
            ))

            db.commit()

            flash(
                "Lección creada correctamente.",
                "success"
            )

            return redirect(
                url_for("admin")
            )

        # -------------------------------------------------
        # CREAR SCRIPT
        # -------------------------------------------------

        if action == "create_script":

            title = request.form.get(
                "title",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            code = request.form.get(
                "code",
                ""
            )

            category = request.form.get(
                "category",
                "Luau"
            ).strip()

            if not title or not description or not code:

                flash(
                    "Completa los campos obligatorios.",
                    "error"
                )

                return redirect(
                    url_for("admin")
                )

            db.execute("""
                INSERT INTO scripts (
                    title,
                    description,
                    code,
                    category,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                title,
                description,
                code,
                category,
                datetime.utcnow().isoformat()
            ))

            db.commit()

            flash(
                "Script creado correctamente.",
                "success"
            )

            return redirect(
                url_for("admin")
            )

        # -------------------------------------------------
        # BLOQUEAR USUARIO
        # -------------------------------------------------

        if action == "block_user":

            user_id = request.form.get(
                "user_id"
            )

            if user_id:

                db.execute("""
                    UPDATE users
                    SET is_blocked = 1
                    WHERE id = ?
                      AND id != ?
                """, (
                    user_id,
                    g.user["id"]
                ))

                db.commit()

                flash(
                    "Usuario bloqueado.",
                    "success"
                )

            return redirect(
                url_for("admin")
            )

        # -------------------------------------------------
        # DESBLOQUEAR USUARIO
        # -------------------------------------------------

        if action == "unblock_user":

            user_id = request.form.get(
                "user_id"
            )

            if user_id:

                db.execute("""
                    UPDATE users
                    SET is_blocked = 0
                    WHERE id = ?
                """, (
                    user_id,
                ))

                db.commit()

                flash(
                    "Usuario desbloqueado.",
                    "success"
                )

            return redirect(
                url_for("admin")
            )

    # -----------------------------------------------------
    # DATOS DEL PANEL
    # -----------------------------------------------------

    users = db.execute("""
        SELECT
            id,
            email,
            is_admin,
            is_blocked,
            created_at
        FROM users
        ORDER BY id DESC
    """).fetchall()

    lessons_list = db.execute("""
        SELECT *
        FROM lessons
        ORDER BY id DESC
    """).fetchall()

    scripts_list = db.execute("""
        SELECT *
        FROM scripts
        ORDER BY id DESC
    """).fetchall()

    return render_template(
        "admin.html",
        users=users,
        lessons=lessons_list,
        scripts=scripts_list
    )


# =========================================================
# ACADEMY AI
# =========================================================

@app.route("/ai")
@login_required
def ai():

    return render_template("ai.html")


@app.route(
    "/api/ai",
    methods=["POST"]
)
@login_required
def api_ai():

    if OpenAI is None:

        return jsonify({
            "ok": False,
            "error": "La librería de OpenAI no está instalada."
        }), 500

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:

        return jsonify({
            "ok": False,
            "error": "OPENAI_API_KEY no está configurada."
        }), 500

    data = request.get_json(
        silent=True
    ) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:

        return jsonify({
            "ok": False,
            "error": "Escribe una pregunta."
        }), 400

    try:

        client = OpenAI(
            api_key=api_key
        )

        model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5-mini"
        )

        response = client.responses.create(

            model=model,

            instructions="""
Eres Academy AI, el profesor de Roblox Studio
y Luau de Academy Blox Script.

Ayuda a los estudiantes a aprender Roblox Studio
desde cero.

Explica de manera sencilla y paso a paso.

Cuando proporciones código Luau:

- Usa código completo.
- Mantén la indentación correcta.
- Explica dónde colocar el script.
- Explica qué hace cada parte importante.
- No inventes funciones de Roblox.
- Si el estudiante tiene un error, explica cómo corregirlo.

Tu objetivo es enseñar, no solamente entregar código.
""",

            input=message
        )

        output = response.output_text

        return jsonify({
            "ok": True,
            "answer": output
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "online"
    })


# =========================================================
# INICIALIZAR BASE DE DATOS
# =========================================================

with app.app_context():
    init_db()


# =========================================================
# EJECUTAR
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
