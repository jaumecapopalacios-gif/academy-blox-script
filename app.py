import sqlite3

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


app = Flask(__name__)

app.secret_key = "academy_secret_key_2026"



# -----------------------
# BASE DE DATOS
# -----------------------

def get_db():

    conn = sqlite3.connect("academy.db")

    conn.row_factory = sqlite3.Row

    return conn



def init_db():

    db = get_db()


    db.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT

    )
    """)


    db.execute("""
    CREATE TABLE IF NOT EXISTS lessons(

        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        content TEXT

    )
    """)


    db.commit()
    db.close()



# -----------------------
# INICIO
# -----------------------

@app.route("/")
def index():

    db = get_db()

    lessons = db.execute(
        "SELECT * FROM lessons"
    ).fetchall()

    db.close()


    return render_template(
        "index.html",
        lessons=lessons,
        current_user=session
    )



# -----------------------
# REGISTRO
# -----------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]

        password = generate_password_hash(
            request.form["password"]
        )


        db = get_db()


        try:

            db.execute(
                """
                INSERT INTO users
                (username,email,password)

                VALUES (?,?,?)
                """,
                (
                    username,
                    email,
                    password
                )
            )


            db.commit()


            flash(
                "Cuenta creada correctamente"
            )


            return redirect(
                url_for("login")
            )


        except:

            flash(
                "Ese usuario ya existe"
            )


        finally:

            db.close()



    return render_template(
        "register.html"
    )



# -----------------------
# LOGIN
# -----------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]


        db = get_db()


        user = db.execute(
            """
            SELECT * FROM users
            WHERE username=?
            """,
            (username,)
        ).fetchone()


        db.close()



        if user and check_password_hash(
            user["password"],
            password
        ):


            session["username"] = user["username"]

            session["email"] = user["email"]

            session["user_id"] = user["id"]

            session["is_admin"] = False


            return redirect(
                url_for("index")
            )



        flash(
            "Usuario o contraseña incorrectos"
        )



    return render_template(
        "login.html"
    )



# -----------------------
# CERRAR SESIÓN
# -----------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )



# -----------------------
# LECCIONES
# -----------------------

@app.route("/lesson/<int:id>")
def lesson(id):

    db = get_db()


    lesson = db.execute(
        """
        SELECT * FROM lessons
        WHERE id=?
        """,
        (id,)
    ).fetchone()


    db.close()



    if not lesson:

        return "Lección no encontrada"



    return render_template(
        "lesson.html",
        lesson=lesson
    )



# -----------------------
# ADMIN
# -----------------------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if "username" not in session:

        return redirect(
            url_for("login")
        )


    db = get_db()



    if request.method == "POST":

        db.execute(
            """
            INSERT INTO lessons
            (title,description,content)

            VALUES (?,?,?)
            """,
            (
                request.form["title"],
                request.form["description"],
                request.form["content"]
            )
        )


        db.commit()



    lessons = db.execute(
        "SELECT * FROM lessons"
    ).fetchall()



    db.close()



    return render_template(
        "admin.html",
        lessons=lessons
    )



# -----------------------
# IA
# -----------------------

@app.route("/ai", methods=["GET", "POST"])
def ai():

    response = None


    if request.method == "POST":

        message = request.form["message"]


        response = (
            "Respuesta de Academy AI: "
            + message
        )



    return render_template(
        "ai.html",
        response=response
    )



# -----------------------

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
