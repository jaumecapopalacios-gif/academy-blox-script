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


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "academy.db")

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    secrets.token_hex(32)
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv(
    "SESSION_COOKIE_SECURE",
    "0"
) == "1"


# ============================================================
# BASE DE DATOS
# ============================================================

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row

    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

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


# ============================================================
# 24 LECCIONES
# ============================================================

def seed_lessons():
    db = get_db()

    count = db.execute(
        "SELECT COUNT(*) FROM lessons"
    ).fetchone()[0]

    if count >= 24:
        return

    lessons = [

        (
            1,
            "Introducción a Roblox Studio",
            "Aprende a utilizar Roblox Studio desde cero y conoce las principales herramientas.",
            """
Roblox Studio es el entorno oficial utilizado para crear experiencias de Roblox.

En esta primera lección aprenderás a reconocer las partes principales del programa.

1. Abre Roblox Studio.
2. Inicia sesión con tu cuenta.
3. Selecciona Baseplate para crear un proyecto.
4. Observa la ventana Explorer.
5. Abre Properties.
6. Localiza Workspace.
7. Busca las herramientas de movimiento.
8. Guarda el proyecto.

Las ventanas más importantes son:

Explorer:
Muestra todos los objetos que existen dentro del juego.

Properties:
Permite modificar las propiedades del objeto seleccionado.

Workspace:
Es el espacio principal donde se encuentran los objetos físicos del mapa.

Output:
Muestra mensajes, advertencias y errores de los scripts.

View:
Permite activar o desactivar diferentes ventanas de Studio.

Una buena costumbre profesional es mantener siempre organizado el Explorer.
No dejes cientos de objetos con nombres como Part, Part1 y Part2.
""",
            "",
            "Roblox Studio"
        ),

        (
            2,
            "Crear tu primer proyecto",
            "Aprende a crear y configurar correctamente un proyecto nuevo.",
            """
En esta lección crearás la estructura inicial de tu juego.

1. Abre Roblox Studio.
2. Selecciona Baseplate.
3. Espera a que cargue el proyecto.
4. Abre Explorer.
5. Abre Properties.
6. Selecciona Workspace.
7. Revisa sus propiedades.

Workspace contiene los objetos físicos del mundo.

Para agregar una pieza:

1. Ve a Home.
2. Pulsa Part.
3. Aparecerá una pieza dentro del mapa.
4. Selecciónala.
5. Usa Move para moverla.
6. Usa Scale para cambiar su tamaño.
7. Usa Rotate para girarla.

Guarda el proyecto frecuentemente.

También puedes utilizar nombres descriptivos:

SpawnPoint
MainFloor
Shop
Enemy
Checkpoint

Esto facilita muchísimo el desarrollo cuando el proyecto crece.
""",
            "",
            "Construcción"
        ),

        (
            3,
            "Parts y construcción",
            "Aprende a construir estructuras utilizando Parts.",
            """
Las Parts son uno de los elementos fundamentales de Roblox Studio.

Puedes crear:

Block
Sphere
Cylinder
Wedge
CornerWedge

Cada Part posee propiedades importantes.

Size:
Define el tamaño.

Position:
Define la posición.

Orientation:
Define la rotación.

Anchored:
Impide que la física mueva la pieza.

CanCollide:
Determina si los jugadores pueden atravesarla.

Para construir una plataforma:

1. Inserta una Part.
2. Activa Anchored.
3. Cambia Size.
4. Coloca la plataforma.
5. Duplica la pieza.
6. Cambia su posición.

Utiliza Ctrl+D para duplicar objetos en PC.

Un desarrollador profesional utiliza piezas reutilizables para construir más rápidamente.
""",
            "",
            "Construcción"
        ),

        (
            4,
            "Materiales y colores",
            "Aprende a utilizar materiales y colores para mejorar tus mapas.",
            """
Los materiales cambian la apariencia de las Parts.

Algunos materiales comunes:

Plastic
Metal
Wood
Glass
Concrete
Brick
Neon

Para cambiar un material:

1. Selecciona una Part.
2. Abre Properties.
3. Busca Material.
4. Selecciona el material deseado.

También puedes cambiar Color.

El material Neon es útil para:

Luces
Señales
Botones
Efectos
Decoraciones futuristas

Evita utilizar demasiados colores diferentes.
Un buen mapa normalmente utiliza una paleta coherente.
""",
            "",
            "Diseño"
        ),

        (
            5,
            "Modelos y organización profesional",
            "Aprende a organizar correctamente un proyecto grande.",
            """
Cuando un juego crece, tener cientos de objetos sin organizar se convierte en un problema.

Utiliza Models y Folders.

Por ejemplo:

Workspace
    Map
    Enemies
    NPCs
    Buildings

ReplicatedStorage
    Modules
    RemoteEvents
    Assets

ServerScriptService
    Systems

StarterGui
    Menus
    HUD

Utiliza nombres claros.

Ejemplo:

Bad:
Part23

Better:
ShopCounter

Best:
MainShopCounter

La organización no cambia directamente el funcionamiento del juego, pero facilita muchísimo encontrar y modificar objetos.
""",
            "",
            "Organización"
        ),

        (
            6,
            "Terrain",
            "Aprende a crear terrenos naturales y mapas más avanzados.",
            """
Terrain permite crear ambientes naturales sin tener que construir cada montaña manualmente.

Puedes crear:

Montañas
Valles
Agua
Ríos
Cuevas
Islas

Abre la herramienta Terrain desde Studio.

Utiliza Generate para crear terreno automáticamente.

Después puedes utilizar:

Draw
Sculpt
Smooth
Paint
Flatten

No generes un mapa enorme sin necesidad.
Los mapas demasiado grandes pueden afectar el rendimiento.

Primero diseña las zonas importantes:

Spawn
Zona principal
Zona de enemigos
Zona de recompensas
Zona final
""",
            "",
            "Construcción"
        ),

        (
            7,
            "Luau desde cero",
            "Aprende los fundamentos del lenguaje utilizado por Roblox.",
            """
Roblox utiliza Luau, un lenguaje basado en Lua.

Una variable almacena información.

Ejemplo:

local nombre = "Jaume"
local monedas = 100

También puedes almacenar valores booleanos:

local tieneEspada = true

Y números:

local velocidad = 16

Utiliza local para declarar variables locales.

Los nombres de las variables deben explicar qué contienen.

Mala práctica:

local x = 100

Mejor:

local playerCoins = 100

El código claro es más fácil de mantener y corregir.
""",
            """local nombre = "Jugador"
local monedas = 100

print(nombre)
print(monedas)""",
            "Luau"
        ),

        (
            8,
            "Scripts y LocalScripts",
            "Aprende dónde colocar scripts y qué función cumple cada uno.",
            """
Roblox tiene diferentes tipos de scripts.

Script:
Se ejecuta principalmente en el servidor.

LocalScript:
Se ejecuta en el cliente del jugador.

ModuleScript:
Permite reutilizar código.

Un Script normalmente puede colocarse en:

ServerScriptService
Workspace
Part

Los LocalScripts suelen utilizarse para:

Interfaces
Controles
Cámara
Entrada del jugador

No pongas información importante únicamente en un LocalScript.
El cliente puede ser manipulado.

La lógica importante debe validarse en el servidor.
""",
            """print("Academy Blox Script iniciado")

local mensaje = "Mi primer script"

print(mensaje)""",
            "Luau"
        ),

        (
            9,
            "Eventos",
            "Aprende a reaccionar cuando ocurren acciones dentro del juego.",
            """
Los eventos permiten ejecutar código cuando sucede algo.

Un ejemplo es Touched.

Una Part puede detectar cuando algo entra en contacto con ella.

También existen:

ProximityPrompt
ClickDetector
MouseClick
Touched
PlayerAdded

Los eventos normalmente utilizan Connect.

Ejemplo:

part.Touched:Connect(function(hit)

end)

Esto significa que cuando la Part detecte un contacto, ejecutará la función.

Los eventos son fundamentales para crear:

Botones
Puertas
Trampas
Checkpoints
Recompensas
""",
            """local part = script.Parent

part.Touched:Connect(function(hit)
    print("La pieza fue tocada")
end)""",
            "Luau"
        ),

        (
            10,
            "Condicionales",
            "Aprende a tomar decisiones dentro de tus scripts.",
            """
Los condicionales permiten que un programa tome decisiones.

La estructura básica es:

if condición then

elseif otra_condición then

else

end

Ejemplo:

Si el jugador tiene 100 monedas, puede comprar.

Si tiene menos, no puede.

Los operadores comunes son:

==
~=
>
<
>=
<=

También puedes utilizar:

and
or
not

La lógica condicional es fundamental para tiendas, puertas, enemigos, misiones y sistemas de recompensa.
""",
            """local monedas = 100

if monedas >= 50 then
    print("Puedes comprar el objeto")
else
    print("No tienes suficientes monedas")
end""",
            "Luau"
        ),

        (
            11,
            "Bucles y funciones",
            "Aprende a repetir acciones y crear código reutilizable.",
            """
Los bucles permiten repetir instrucciones.

Ejemplo:

for i = 1, 5 do
    print(i)
end

También existe while.

Las funciones permiten guardar instrucciones reutilizables.

Ejemplo:

local function saludar()
    print("Hola")
end

saludar()

Puedes pasar información a una función:

local function sumar(a, b)
    return a + b
end

Las funciones son esenciales para evitar copiar el mismo código muchas veces.
""",
            """local function sumar(a, b)
    return a + b
end

local resultado = sumar(10, 20)

print(resultado)""",
            "Luau"
        ),

        (
            12,
            "Tablas y datos",
            "Aprende a almacenar grupos de información.",
            """
Las tablas son una de las estructuras más importantes de Luau.

Puedes utilizarlas como listas:

local armas = {
    "Espada",
    "Arco",
    "Pistola"
}

También puedes utilizar claves:

local jugador = {
    nombre = "Jugador",
    monedas = 100,
    nivel = 5
}

Puedes acceder a los datos:

print(jugador.nombre)
print(jugador.monedas)

Las tablas aparecen constantemente en sistemas de:

Inventarios
Tiendas
Configuraciones
Jugadores
Misiones
""",
            """local jugador = {
    nombre = "Jugador",
    monedas = 100,
    nivel = 1
}

print(jugador.nombre)
print(jugador.monedas)""",
            "Luau"
        ),

        (
            13,
            "Sistema de checkpoints",
            "Construye un sistema básico de checkpoints.",
            """
Los checkpoints permiten guardar el progreso temporal del jugador.

Un sistema básico puede funcionar así:

1. El jugador toca un checkpoint.
2. Se guarda el checkpoint actual.
3. Si muere, reaparece en ese lugar.

Puedes colocar varios checkpoints:

Checkpoint1
Checkpoint2
Checkpoint3

Es importante evitar que cualquier jugador pueda cambiar datos importantes sin validación.

Los checkpoints son útiles para:

Obbys
Juegos de aventura
Juegos de plataformas
Mapas de carreras
""",
            """local checkpoint = script.Parent

checkpoint.Touched:Connect(function(hit)
    local character = hit.Parent
    local humanoid = character:FindFirstChild("Humanoid")

    if humanoid then
        print("Checkpoint alcanzado")
    end
end)""",
            "Sistemas"
        ),

        (
            14,
            "Sistema de monedas",
            "Crea un sistema básico de monedas recolectables.",
            """
Las monedas son una mecánica muy común.

Una moneda puede:

Aparecer en el mapa.
Detectar al jugador.
Aumentar su cantidad.
Desaparecer.
Volver a aparecer después de cierto tiempo.

El servidor debe controlar la recompensa.

No debes confiar en que el cliente diga:

"Yo recogí 999 monedas."

El servidor debe comprobar que realmente ocurrió la acción.
""",
            """local coin = script.Parent
local collected = false

coin.Touched:Connect(function(hit)

    if collected then
        return
    end

    local humanoid = hit.Parent:FindFirstChild("Humanoid")

    if humanoid then
        collected = true

        print("Moneda recogida")

        coin.Transparency = 1
        coin.CanCollide = false
    end
end)""",
            "Sistemas"
        ),

        (
            15,
            "Leaderstats",
            "Aprende a mostrar estadísticas de los jugadores.",
            """
Leaderstats permite mostrar estadísticas en la tabla de jugadores.

Puedes utilizarlo para:

Coins
Wins
Level
Kills
Points

Ejemplo:

El jugador entra.
Se crea una carpeta leaderstats.
Se añade Coins.
El valor aparece en la lista de jugadores.

El servidor debe controlar estos valores.
""",
            """local Players = game:GetService("Players")

Players.PlayerAdded:Connect(function(player)

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
            16,
            "Interfaces GUI",
            "Aprende a crear interfaces para tus jugadores.",
            """
Las interfaces permiten mostrar información en pantalla.

Los objetos principales incluyen:

ScreenGui
Frame
TextLabel
TextButton
ImageLabel
ImageButton

Una interfaz puede utilizarse para:

Menús
Vida
Monedas
Inventario
Configuración
Misiones

Mantén una jerarquía organizada.

Ejemplo:

ScreenGui
    MainFrame
        Title
        PlayButton
        SettingsButton

Utiliza nombres descriptivos.
""",
            """local button = script.Parent

button.MouseButton1Click:Connect(function()
    print("Botón pulsado")
end)""",
            "GUI"
        ),

        (
            17,
            "Menús profesionales",
            "Crea un menú principal organizado y moderno.",
            """
Un menú profesional normalmente contiene:

Título del juego
Botón Play
Botón Settings
Botón Credits

Puedes ocultar y mostrar Frames utilizando Visible.

Ejemplo:

mainMenu.Visible = false

También puedes crear animaciones utilizando TweenService.

Los menús deben ser:

Claros
Rápidos
Legibles
Adaptables a diferentes pantallas

No llenes la pantalla de botones innecesarios.
""",
            """local TweenService = game:GetService("TweenService")

local frame = script.Parent

local objetivo = {
    Position = UDim2.new(0.5, 0, 0.5, 0)
}

local informacion = TweenInfo.new(
    0.5,
    Enum.EasingStyle.Quad,
    Enum.EasingDirection.Out
)

local tween = TweenService:Create(
    frame,
    informacion,
    objetivo
)

tween:Play()""",
            "GUI"
        ),

        (
            18,
            "Tiendas",
            "Aprende a crear una tienda dentro de tu juego.",
            """
Una tienda necesita:

Objetos
Precios
Moneda
Botones
Validación
Recompensa

La compra debe verificarse en el servidor.

El cliente puede solicitar:

"Quiero comprar la espada."

Pero el servidor debe comprobar:

¿Tiene suficientes monedas?
¿Existe el objeto?
¿Puede comprarlo?
¿Ya lo tiene?

Nunca confíes únicamente en los valores enviados por el cliente.
""",
            """local price = 100
local coins = 150

if coins >= price then
    coins -= price
    print("Compra realizada")
else
    print("No tienes suficientes monedas")
end""",
            "Sistemas"
        ),

        (
            19,
            "RemoteEvents",
            "Aprende a comunicar el cliente con el servidor.",
            """
RemoteEvents permiten enviar información entre cliente y servidor.

Se utilizan mucho para:

Botones
Compras
Habilidades
Interacciones
Sistemas de combate

Normalmente se colocan en ReplicatedStorage.

El cliente puede enviar una solicitud.

El servidor recibe la solicitud y valida los datos.

Nunca hagas que el cliente controle directamente una recompensa importante.
""",
            """local ReplicatedStorage = game:GetService("ReplicatedStorage")

local evento = ReplicatedStorage:WaitForChild("MiEvento")

evento.OnServerEvent:Connect(function(player)
    print(player.Name .. " activó el evento")
end)""",
            "Programación avanzada"
        ),

        (
            20,
            "DataStore",
            "Aprende los fundamentos para guardar el progreso.",
            """
DataStore permite guardar datos entre sesiones.

Puede guardar:

Monedas
Nivel
Inventario
Victorias
Progreso

Un sistema profesional debe:

Cargar los datos.
Usar los datos.
Guardar los datos.
Manejar errores.
Evitar perder información.

No debes guardar información constantemente sin control.

Utiliza técnicas de protección y validación.
""",
            """local DataStoreService = game:GetService("DataStoreService")

local datos = DataStoreService:GetDataStore("PlayerData")

local success, result = pcall(function()
    return datos:GetAsync("Player_123")
end)

if success then
    print("Datos cargados")
else
    warn("No se pudieron cargar los datos")
end""",
            "Datos"
        ),

        (
            21,
            "Sistemas avanzados",
            "Aprende a combinar diferentes sistemas para crear mecánicas complejas.",
            """
Ahora puedes combinar:

Inventario
Monedas
GUI
RemoteEvents
DataStore
Leaderstats

Un inventario puede utilizar tablas para guardar objetos.

Ejemplo:

Espada
Arco
Poción

Después puedes mostrar estos objetos mediante una GUI.

Los sistemas grandes deben dividirse en diferentes scripts o ModuleScripts.

Evita crear un único script de miles de líneas.
""",
            """local Inventory = {}

function Inventory.AddItem(player, itemName)
    print("Añadiendo:", itemName)
end

function Inventory.RemoveItem(player, itemName)
    print("Eliminando:", itemName)
end

return Inventory""",
            "Programación avanzada"
        ),

        (
            22,
            "Seguridad y Anti-Exploit",
            "Aprende principios básicos para proteger tus sistemas.",
            """
La seguridad es una parte fundamental del desarrollo.

Nunca confíes en el cliente.

Un exploit puede intentar modificar:

Dinero
Velocidad
Daño
Inventario
Teletransporte

El servidor debe validar las acciones importantes.

Ejemplo:

Si una espada cuesta 100 monedas, el servidor debe comprobar que el jugador tiene 100 monedas.

No basta con ocultar el precio dentro de un LocalScript.

También debes controlar RemoteEvents y comprobar los argumentos recibidos.

La seguridad no significa intentar detectar absolutamente todo.
Significa diseñar los sistemas para que las solicitudes falsas no puedan conceder ventajas injustificadas.
""",
            """local function compraValida(player, precio)

    local leaderstats = player:FindFirstChild("leaderstats")

    if not leaderstats then
        return false
    end

    local coins = leaderstats:FindFirstChild("Coins")

    if not coins then
        return false
    end

    return coins.Value >= precio
end""",
            "Seguridad"
        ),

        (
            23,
            "Optimización",
            "Aprende a mejorar el rendimiento de tus juegos.",
            """
Un juego bonito también debe funcionar correctamente.

Problemas comunes:

Demasiadas Parts.
Scripts innecesarios.
Bucles infinitos.
Modelos demasiado pesados.
Demasiadas partículas.
Demasiados eventos.

Consejos:

Organiza los scripts.
Evita while true sin necesidad.
Desconecta eventos cuando ya no sean necesarios.
Reduce objetos innecesarios.
Prueba el juego en diferentes dispositivos.

Utiliza las herramientas de análisis de rendimiento de Roblox Studio.

Optimizar no significa eliminar todo.
Significa utilizar los recursos donde realmente aportan algo.
""",
            """-- Evita hacer esto sin necesidad:

while true do
    task.wait()
    print("Ejecutando...")
end

-- Utiliza tareas controladas y evita
-- procesos que no tengan una función real.""",
            "Optimización"
        ),

        (
            24,
            "Crear y publicar un juego",
            "Aprende a preparar tu proyecto para publicarlo.",
            """
Esta es la lección final.

Antes de publicar debes probar:

Movimiento
Interfaz
Compras
Respawn
Checkpoints
Guardado
Errores
Rendimiento

Prueba con varios jugadores cuando sea posible.

Revisa el nombre del juego.
Escribe una descripción clara.
Utiliza imágenes apropiadas.
Configura correctamente la experiencia.

Antes de publicar una actualización:

1. Haz una copia.
2. Prueba los cambios.
3. Revisa Output.
4. Comprueba los sistemas importantes.
5. Publica la versión.

Después de publicar, continúa revisando errores y comentarios.

Un juego profesional no se termina cuando se publica.
Se sigue desarrollando.
""",
            """print("Academy Blox Script - Proyecto final")

local version = "1.0.0"

print("Versión:", version)
print("Proyecto preparado para pruebas.")""",
            "Proyecto final"
        )
    ]

    for lesson in lessons:
        exists = db.execute(
            "SELECT id FROM lessons WHERE id = ?",
            (lesson[0],)
        ).fetchone()

        if not exists:
            db.execute("""
                INSERT INTO lessons
                (id, title, description, content, code, category, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                lesson[0],
                lesson[1],
                lesson[2],
                lesson[3],
                lesson[4],
                lesson[5],
                datetime.utcnow().isoformat()
            ))

    db.commit()


# ============================================================
# SCRIPTS DE EJEMPLO
# ============================================================

def seed_scripts():
    db = get_db()

    count = db.execute(
        "SELECT COUNT(*) FROM scripts"
    ).fetchone()[0]

    if count > 0:
        return

    scripts = [
        (
            "Sistema de Leaderstats",
            "Crea monedas visibles en la tabla de jugadores.",
            """local Players = game:GetService("Players")

Players.PlayerAdded:Connect(function(player)

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
            "Puerta con ProximityPrompt",
            "Permite abrir una puerta acercándose a ella.",
            """local prompt = script.Parent:WaitForChild("ProximityPrompt")

prompt.Triggered:Connect(function(player)
    print(player.Name .. " abrió la puerta")
end)""",
            "Interacciones"
        ),
        (
            "Parte que elimina al jugador",
            "Ejemplo de una zona peligrosa.",
            """local part = script.Parent

part.Touched:Connect(function(hit)

    local humanoid = hit.Parent:FindFirstChild("Humanoid")

    if humanoid then
        humanoid.Health = 0
    end

end)""",
            "Obby"
        ),
        (
            "Dar monedas al tocar una pieza",
            "Entrega una recompensa cuando el jugador toca la pieza.",
            """local part = script.Parent

part.Touched:Connect(function(hit)

    local player = game.Players:GetPlayerFromCharacter(hit.Parent)

    if not player then
        return
    end

    local leaderstats = player:FindFirstChild("leaderstats")

    if not leaderstats then
        return
    end

    local coins = leaderstats:FindFirstChild("Coins")

    if coins then
        coins.Value += 10
    end

end)""",
            "Economía"
        ),
        (
            "Botón GUI",
            "Detecta cuando un jugador pulsa un botón.",
            """local button = script.Parent

button.MouseButton1Click:Connect(function()

    print("Botón pulsado")

end)""",
            "GUI"
        ),
        (
            "Mensaje al entrar",
            "Muestra información cuando un jugador entra.",
            """local Players = game:GetService("Players")

Players.PlayerAdded:Connect(function(player)

    print("Bienvenido " .. player.Name)

end)""",
            "Básico"
        )
    ]

    for script_data in scripts:
        db.execute("""
            INSERT INTO scripts
            (title, description, code, category, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            script_data[0],
            script_data[1],
            script_data[2],
            script_data[3],
            datetime.utcnow().isoformat()
        ))

    db.commit()


# ============================================================
# USUARIO ACTUAL
# ============================================================

@app.before_request
def load_user():
    g.user = None

    user_id = session.get("user_id")

    if user_id:
        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if user and not user["is_blocked"]:
            g.user = user
        else:
            session.clear()


@app.context_processor
def inject_user():
    return {
        "user": g.user,
        "logged_in": g.user is not None
    }


# ============================================================
# DECORADORES
# ============================================================

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if g.user is None:
            flash("Debes iniciar sesión primero.", "error")
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if g.user is None:
            flash("Debes iniciar sesión.", "error")
            return redirect(url_for("login"))

        if not g.user["is_admin"]:
            flash("No tienes permisos de administrador.", "error")
            return redirect(url_for("index"))

        return view(*args, **kwargs)

    return wrapped_view


# ============================================================
# INICIO
# ============================================================

@app.route("/")
def index():

    db = get_db()

    lessons = db.execute("""
        SELECT *
        FROM lessons
        ORDER BY id ASC
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


# ============================================================
# REGISTRO
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if len(username) < 3:
            flash("El usuario debe tener al menos 3 caracteres.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return redirect(url_for("register"))

        db = get_db()

        exists = db.execute("""
            SELECT id
            FROM users
            WHERE username = ? OR email = ?
        """, (username, email)).fetchone()

        if exists:
            flash("El usuario o correo ya está registrado.", "error")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        db.execute("""
            INSERT INTO users
            (username, email, password_hash, is_admin, is_blocked, created_at)
            VALUES (?, ?, ?, 0, 0, ?)
        """, (
            username,
            email,
            password_hash,
            datetime.utcnow().isoformat()
        ))

        db.commit()

        flash("Cuenta creada correctamente.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        login_value = request.form.get("login", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()

        user = db.execute("""
            SELECT *
            FROM users
            WHERE lower(email) = ?
               OR lower(username) = ?
        """, (
            login_value,
            login_value
        )).fetchone()

        if not user:
            flash("Usuario o contraseña incorrectos.", "error")
            return redirect(url_for("login"))

        if user["is_blocked"]:
            flash("Esta cuenta está bloqueada.", "error")
            return redirect(url_for("login"))

        if not check_password_hash(
            user["password_hash"],
            password
        ):
            flash("Usuario o contraseña incorrectos.", "error")
            return redirect(url_for("login"))

        session.clear()

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["email"] = user["email"]
        session["is_admin"] = bool(user["is_admin"])

        flash("Has iniciado sesión correctamente.", "success")

        return redirect(url_for("index"))

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    flash("Sesión cerrada.", "success")

    return redirect(url_for("index"))


# ============================================================
# LECCIONES
# ============================================================

@app.route("/lessons")
@login_required
def lessons():

    db = get_db()

    all_lessons = db.execute("""
        SELECT *
        FROM lessons
        ORDER BY id ASC
    """).fetchall()

    return render_template(
        "lessons.html",
        lessons=all_lessons
    )


@app.route("/lesson/<int:lesson_id>")
@login_required
def lesson(lesson_id):

    db = get_db()

    current = db.execute(
        "SELECT * FROM lessons WHERE id = ?",
        (lesson_id,)
    ).fetchone()

    if not current:
        flash("Lección no encontrada.", "error")
        return redirect(url_for("lessons"))

    previous = db.execute("""
        SELECT id, title
        FROM lessons
        WHERE id < ?
        ORDER BY id DESC
        LIMIT 1
    """, (lesson_id,)).fetchone()

    next_lesson = db.execute("""
        SELECT id, title
        FROM lessons
        WHERE id > ?
        ORDER BY id ASC
        LIMIT 1
    """, (lesson_id,)).fetchone()

    return render_template(
        "lesson.html",
        lesson=current,
        previous=previous,
        next_lesson=next_lesson
    )


# ============================================================
# SCRIPTS
# ============================================================

@app.route("/scripts")
@login_required
def scripts():

    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    db = get_db()

    query = "SELECT * FROM scripts WHERE 1=1"
    params = []

    if search:
        query += """
            AND (
                title LIKE ?
                OR description LIKE ?
                OR code LIKE ?
            )
        """

        value = f"%{search}%"

        params.extend([
            value,
            value,
            value
        ])

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY id DESC"

    all_scripts = db.execute(
        query,
        params
    ).fetchall()

    categories = db.execute("""
        SELECT DISTINCT category
        FROM scripts
        ORDER BY category
    """).fetchall()

    return render_template(
        "scripts.html",
        scripts=all_scripts,
        categories=categories,
        search=search,
        category=category
    )


# ============================================================
# ACTIVAR ADMIN
# ============================================================

@app.route("/activate-admin", methods=["GET", "POST"])
@login_required
def activate_admin():

    if g.user["is_admin"]:
        flash("Ya eres administrador.", "success")
        return redirect(url_for("admin"))

    if request.method == "POST":

        code = request.form.get("code", "")

        admin_code = os.getenv(
            "ADMIN_CODE",
            "CAMBIA-ESTE-CODIGO"
        )

        if code != admin_code:
            flash("Código incorrecto.", "error")
            return redirect(url_for("activate_admin"))

        db = get_db()

        db.execute("""
            UPDATE users
            SET is_admin = 1
            WHERE id = ?
        """, (g.user["id"],))

        db.commit()

        session["is_admin"] = True

        flash(
            "Administrador activado correctamente.",
            "success"
        )

        return redirect(url_for("admin"))

    return """
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Activar administrador | Academy Blox Script</title>
        <style>
            * { box-sizing: border-box; }
            body {
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #05070b;
                color: #fff;
                font-family: Arial, sans-serif;
                padding: 20px;
            }
            .card {
                width: 100%;
                max-width: 430px;
                background: #0b111a;
                border: 1px solid #00e5ff;
                border-radius: 18px;
                padding: 30px;
                box-shadow: 0 0 30px rgba(0,229,255,.18);
            }
            h1 {
                margin-top: 0;
                color: #00e5ff;
                text-align: center;
            }
            p {
                color: #b8c4d1;
                text-align: center;
                line-height: 1.5;
            }
            input {
                width: 100%;
                padding: 14px;
                margin: 18px 0 12px;
                border-radius: 10px;
                border: 1px solid #263544;
                background: #05070b;
                color: white;
                outline: none;
            }
            button {
                width: 100%;
                padding: 14px;
                border: 0;
                border-radius: 10px;
                background: #00e5ff;
                color: #001018;
                font-weight: bold;
                cursor: pointer;
            }
            .back {
                display: block;
                margin-top: 16px;
                text-align: center;
                color: #00e5ff;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Activar administrador</h1>
            <p>Introduce el código de administrador configurado en Render.</p>
            <form method="POST">
                <input
                    type="password"
                    name="code"
                    placeholder="Código de administrador"
                    autocomplete="off"
                    required
                >
                <button type="submit">Activar administrador</button>
            </form>
            <a class="back" href="/">Volver al inicio</a>
        </div>
    </body>
    </html>
    """


# ============================================================
# ADMIN
# ============================================================

@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():

    db = get_db()

    if request.method == "POST":

        action = request.form.get("action")

        # ----------------------------------------------------
        # CREAR LECCIÓN
        # ----------------------------------------------------

        if action == "create_lesson":

            title = request.form.get("title", "").strip()
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

            if title and description and content:

                db.execute("""
                    INSERT INTO lessons
                    (title, description, content, code, category, created_at)
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

        # ----------------------------------------------------
        # CREAR SCRIPT
        # ----------------------------------------------------

        elif action == "create_script":

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

            if title and description and code:

                db.execute("""
                    INSERT INTO scripts
                    (title, description, code, category, created_at)
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

        # ----------------------------------------------------
        # BLOQUEAR USUARIO
        # ----------------------------------------------------

        elif action == "block_user":

            user_id = request.form.get("user_id")

            if user_id:

                db.execute("""
                    UPDATE users
                    SET is_blocked = 1
                    WHERE id = ?
                """, (user_id,))

                db.commit()

                flash(
                    "Usuario bloqueado.",
                    "success"
                )

        # ----------------------------------------------------
        # DESBLOQUEAR USUARIO
        # ----------------------------------------------------

        elif action == "unblock_user":

            user_id = request.form.get("user_id")

            if user_id:

                db.execute("""
                    UPDATE users
                    SET is_blocked = 0
                    WHERE id = ?
                """, (user_id,))

                db.commit()

                flash(
                    "Usuario desbloqueado.",
                    "success"
                )

        return redirect(url_for("admin"))

    users = db.execute("""
        SELECT id, username, email, is_admin,
               is_blocked, created_at
        FROM users
        ORDER BY id DESC
    """).fetchall()

    lessons_list = db.execute("""
        SELECT *
        FROM lessons
        ORDER BY id ASC
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


# ============================================================
# ACADEMY AI
# ============================================================

@app.route("/ai")
@login_required
def ai():

    return render_template("ai.html")


@app.route("/api/ai", methods=["POST"])
@login_required
def api_ai():

    data = request.get_json(silent=True) or {}

    messages = data.get("messages", [])

    if not isinstance(messages, list):
        return jsonify({
            "error": "Formato incorrecto."
        }), 400

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or OpenAI is None:

        return jsonify({
            "answer": (
                "Academy AI está instalado, pero todavía no "
                "tiene configurada la OPENAI_API_KEY en Render. "
                "El resto de Academy Blox Script funciona "
                "normalmente."
            )
        })

    try:

        client = OpenAI(api_key=api_key)

        safe_messages = []

        for message in messages[-12:]:

            if not isinstance(message, dict):
                continue

            role = message.get("role")

            content = message.get("content")

            if role not in ["user", "assistant"]:
                continue

            if not isinstance(content, str):
                continue

            safe_messages.append({
                "role": role,
                "content": content[:4000]
            })

        response = client.responses.create(
            model=os.getenv(
                "OPENAI_MODEL",
                "gpt-5-mini"
            ),
            instructions=(
                "Eres Academy AI, un profesor especializado "
                "en Roblox Studio y Luau. Explica programación "
                "de forma clara para estudiantes. Enseña "
                "paso a paso, proporciona ejemplos seguros "
                "y ayuda a corregir errores de código."
            ),
            input=safe_messages
        )

        return jsonify({
            "answer": response.output_text
        })

    except Exception as error:

        print("ERROR ACADEMY AI:", error)

        return jsonify({
            "error": (
                "No se pudo conectar con Academy AI. "
                "Comprueba la configuración de OpenAI."
            )
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "online",
        "academy": "Academy Blox Script"
    })


# ============================================================
# INICIAR BASE DE DATOS
# ============================================================

with app.app_context():
    init_db()


# ============================================================
# EJECUCIÓN LOCAL
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "5000")
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
