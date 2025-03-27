import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import webbrowser
from threading import Timer
from datetime import date

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Clave para manejar sesiones

# Configuración de conexión a MySQL
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="root",
    database="fitgo"
)
cursor = db.cursor(dictionary=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/play')
def play():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))  # Redirigir si no está logueado

    id_usuario = session['id_usuario']
    cursor.execute("SELECT monedas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    usuario = cursor.fetchone()
    monedas = usuario['monedas'] if usuario else 0

    return render_template('play.html', monedas=monedas)

@app.route('/get_monedas', methods=['GET'])
def get_monedas():
    if 'id_usuario' not in session:
        return jsonify({'success': False, 'message': 'Usuario no logueado'}), 401

    id_usuario = session['id_usuario']
    cursor.execute("SELECT monedas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    usuario = cursor.fetchone()

    if not usuario:
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

    return jsonify({'success': True, 'monedas': usuario['monedas']})

@app.route('/complete_exercise', methods=['POST'])
def complete_exercise():
    if 'id_usuario' not in session:
        return jsonify({'success': False, 'message': 'Usuario no logueado'}), 401

    id_usuario = session['id_usuario']
    exercise_type = request.form['exercise_type']
    fecha_actual = date.today()

    # Mapear el nombre del ejercicio a un id_ejercicio
    exercise_mapping = {
        'Sentadillas': 1,
        'Flexiones': 2,
        'Abdominales': 3
    }
    id_ejercicio = exercise_mapping.get(exercise_type)
    if not id_ejercicio:
        return jsonify({'success': False, 'message': 'Ejercicio no encontrado'}), 400

    # Mapear el ejercicio a su tipo de estadística
    stat_mapping = {
        'Sentadillas': 'fuerza',
        'Flexiones': 'fuerza',
        'Abdominales': 'resistencia'
    }
    stat_type = stat_mapping.get(exercise_type)
    if not stat_type:
        return jsonify({'success': False, 'message': 'Tipo de estadística no encontrado para este ejercicio'}), 400

    try:
        # Registrar el ejercicio en rutina_ejercicios
        cursor.execute("INSERT INTO rutina_ejercicios (id_usuario, id_ejercicio, fecha_inicio, fecha_fin) VALUES (%s, %s, %s, %s)",
                       (id_usuario, id_ejercicio, fecha_actual, fecha_actual))

        # Verificar las monedas actuales del usuario
        cursor.execute("SELECT monedas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        usuario = cursor.fetchone()
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

        monedas_actuales = usuario['monedas']
        print(f"Monedas actuales antes de sumar: {monedas_actuales}")  # Depuración

        # Sumar 100 monedas al usuario
        cursor.execute("UPDATE usuarios SET monedas = monedas + 100 WHERE id_usuario = %s", (id_usuario,))

        # Incrementar la estadística correspondiente (fuerza, agilidad o resistencia)
        cursor.execute(f"UPDATE usuarios SET {stat_type} = {stat_type} + 10 WHERE id_usuario = %s", (id_usuario,))

        db.commit()

        # Verificar las monedas después de la actualización
        cursor.execute("SELECT monedas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        usuario_actualizado = cursor.fetchone()
        print(f"Monedas después de sumar: {usuario_actualizado['monedas']}")  # Depuración

        return jsonify({'success': True, 'message': 'Monedas y estadísticas actualizadas con éxito'})
    except mysql.connector.Error as err:
        db.rollback()  # Revertir cambios en caso de error
        print(f"Error en la base de datos: {err}")
        return jsonify({'success': False, 'message': 'Error al procesar el ejercicio'}), 500

@app.route('/store')
def store():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))  # Redirigir si no está logueado

    id_usuario = session['id_usuario']

    # Obtener los productos disponibles
    cursor.execute("SELECT * FROM productos WHERE stock > 0")  # Solo productos con stock disponible
    products = cursor.fetchall()

    # Obtener las monedas del usuario
    cursor.execute("SELECT monedas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    usuario = cursor.fetchone()
    monedas = usuario['monedas'] if usuario else 0

    # Obtener el carrito de la sesión (si existe)
    carrito = session.get('carrito', [])

    # Calcular el total de monedas necesarias para los ítems en el carrito
    total_carrito = 0
    carrito_con_detalles = []
    for item in carrito:
        cursor.execute("SELECT * FROM productos WHERE id = %s", (item['id'],))
        producto = cursor.fetchone()
        if producto:
            total_carrito += producto['precio'] * item['cantidad']
            carrito_con_detalles.append({
                'id': producto['id'],
                'nombre': producto['nombre'],
                'precio': producto['precio'],
                'cantidad': item['cantidad']
            })

    return render_template('store.html', products=products, monedas=monedas, carrito=carrito_con_detalles, total_carrito=total_carrito)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    producto_id = int(request.form['producto_id'])
    cantidad = int(request.form['cantidad'])

    # Verificar el stock del producto
    cursor.execute("SELECT stock FROM productos WHERE id = %s", (producto_id,))
    producto = cursor.fetchone()
    if not producto or producto['stock'] < cantidad:
        flash("No hay suficiente stock disponible para este producto.")
        return redirect(url_for('store'))

    # Obtener el carrito de la sesión o inicializar uno nuevo
    carrito = session.get('carrito', [])

    # Verificar si el producto ya está en el carrito
    for item in carrito:
        if item['id'] == producto_id:
            # Verificar si la cantidad total (en el carrito + nueva cantidad) excede el stock
            if producto['stock'] < (item['cantidad'] + cantidad):
                flash("No puedes añadir más unidades de este producto, el stock es insuficiente.")
                return redirect(url_for('store'))
            item['cantidad'] += cantidad
            break
    else:
        # Si no está, añadirlo
        carrito.append({'id': producto_id, 'cantidad': cantidad})

    # Guardar el carrito actualizado en la sesión
    session['carrito'] = carrito

    return redirect(url_for('store'))

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    # Vaciar el carrito en la sesión
    session['carrito'] = []
    flash("¡Carrito vaciado con éxito!")
    return redirect(url_for('store'))

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    id_usuario = session['id_usuario']
    carrito = session.get('carrito', [])

    if not carrito:
        flash("El carrito está vacío.")
        return redirect(url_for('store'))

    # Verificar el stock de todos los productos en el carrito
    for item in carrito:
        cursor.execute("SELECT stock, nombre FROM productos WHERE id = %s", (item['id'],))
        producto = cursor.fetchone()
        if not producto or producto['stock'] < item['cantidad']:
            flash(f"No hay suficiente stock para {producto['nombre']}. Por favor, ajusta tu carrito.")
            return redirect(url_for('store'))

    # Calcular el total de monedas necesarias
    total_carrito = 0
    for item in carrito:
        cursor.execute("SELECT precio FROM productos WHERE id = %s", (item['id'],))
        producto = cursor.fetchone()
        if producto:
            total_carrito += producto['precio'] * item['cantidad']

    # Verificar si el usuario tiene suficientes monedas
    cursor.execute("SELECT monedas FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    usuario = cursor.fetchone()
    monedas = usuario['monedas'] if usuario else 0

    if monedas < total_carrito:
        flash("No tienes suficientes monedas para completar la compra.")
        return redirect(url_for('store'))

    # Registrar la compra y actualizar el stock e inventario
    for item in carrito:
        # Registrar la compra en la tabla 'compras'
        cursor.execute("INSERT INTO compras (id_usuario, id_producto, cantidad) VALUES (%s, %s, %s)",
                       (id_usuario, item['id'], item['cantidad']))

        # Actualizar el stock del producto
        cursor.execute("UPDATE productos SET stock = stock - %s WHERE id = %s", (item['cantidad'], item['id']))

        # Actualizar el inventario del usuario
        cursor.execute("SELECT cantidad FROM inventario WHERE id_usuario = %s AND id_producto = %s", (id_usuario, item['id']))
        inventario = cursor.fetchone()
        if inventario:
            # Si el producto ya está en el inventario, incrementar la cantidad
            cursor.execute("UPDATE inventario SET cantidad = cantidad + %s WHERE id_usuario = %s AND id_producto = %s",
                           (item['cantidad'], id_usuario, item['id']))
        else:
            # Si no está, añadirlo al inventario
            cursor.execute("INSERT INTO inventario (id_usuario, id_producto, cantidad) VALUES (%s, %s, %s)",
                           (id_usuario, item['id'], item['cantidad']))

    # Restar las monedas al usuario
    cursor.execute("UPDATE usuarios SET monedas = monedas - %s WHERE id_usuario = %s", (total_carrito, id_usuario))
    db.commit()

    # Limpiar el carrito
    session['carrito'] = []

    flash("¡Compra realizada con éxito!")
    return redirect(url_for('store'))

@app.route('/diets')
def diets():
    return render_template('diets.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nickname = request.form['nickname']
        password = request.form['password']
        password_hash = generate_password_hash(password)  # Encriptar contraseña

        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nickname, password_hash, monedas) VALUES (%s, %s, %s)", (nickname, password_hash, 0))
            db.commit()
            return redirect(url_for('login'))  # Redirige al login
        except mysql.connector.IntegrityError:
            return "El nickname ya está en uso. Intenta otro."
        finally:
            cursor.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nickname = request.form['nickname']
        password = request.form['password']

        cursor.execute("SELECT * FROM usuarios WHERE nickname = %s", (nickname,))
        usuario = cursor.fetchone()

        if usuario and check_password_hash(usuario['password_hash'], password):
            session['id_usuario'] = usuario['id_usuario']  # Guardar usuario en sesión
            return redirect(url_for('profile'))
        else:
            return "Usuario o contraseña incorrectos."

    return render_template('login.html')

@app.route('/missions')
def missions():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))  # Redirigir si no está logueado

    id_usuario = session['id_usuario']

    # Obtener todas las misiones
    cursor.execute("SELECT * FROM misiones")
    misiones = cursor.fetchall()

    # Obtener las misiones completadas por el usuario
    cursor.execute("""
        SELECT m.* FROM misiones m
        JOIN logros_misiones lm ON m.id_mision = lm.id_mision
        WHERE lm.id_usuario = %s
    """, (id_usuario,))
    misiones_completadas = cursor.fetchall()

    # Obtener las misiones pendientes (no completadas)
    cursor.execute("""
        SELECT m.* FROM misiones m
        WHERE m.id_mision NOT IN (
            SELECT id_mision FROM logros_misiones WHERE id_usuario = %s
        )
    """, (id_usuario,))
    misiones_pendientes = cursor.fetchall()

    # Obtener los ejercicios divididos por categorías
    cursor.execute("SELECT * FROM ejercicios WHERE tipo = 'fuerza'")
    ejercicios_fuerza = cursor.fetchall()

    cursor.execute("SELECT * FROM ejercicios WHERE tipo = 'agilidad'")
    ejercicios_agilidad = cursor.fetchall()

    cursor.execute("SELECT * FROM ejercicios WHERE tipo = 'resistencia'")
    ejercicios_resistencia = cursor.fetchall()

    return render_template('missions.html', 
                           misiones=misiones, 
                           misiones_completadas=misiones_completadas, 
                           misiones_pendientes=misiones_pendientes,
                           ejercicios_fuerza=ejercicios_fuerza, 
                           ejercicios_agilidad=ejercicios_agilidad, 
                           ejercicios_resistencia=ejercicios_resistencia)

@app.route('/completar_ejercicio', methods=['POST'])
def completar_ejercicio():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    id_usuario = session['id_usuario']
    id_ejercicio = request.form['id_ejercicio']

    # Obtener el tipo del ejercicio
    cursor.execute("SELECT tipo FROM ejercicios WHERE id_ejercicio = %s", (id_ejercicio,))
    ejercicio = cursor.fetchone()

    if not ejercicio:
        return "Error: Ejercicio no encontrado"

    tipo = ejercicio['tipo']

    # Registrar en la tabla rutina_ejercicios
    fecha_actual = date.today()
    cursor.execute("INSERT INTO rutina_ejercicios (id_usuario, id_ejercicio, fecha_inicio, fecha_fin) VALUES (%s, %s, %s, %s)",
                   (id_usuario, id_ejercicio, fecha_actual, fecha_actual))

    # Incrementar el atributo correspondiente (fuerza, agilidad o resistencia)
    cursor.execute(f"UPDATE usuarios SET {tipo} = {tipo} + 10 WHERE id_usuario = %s", (id_usuario,))
    
    db.commit()

    return redirect(url_for('missions'))

@app.route('/verificar_misiones')
def verificar_misiones():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    id_usuario = session['id_usuario']

    connection = mysql.connector.connect(host="127.0.0.1", user="root", password="root", database="fitgo")
    cursor = connection.cursor(dictionary=True)

    cursor.execute(""" 
        SELECT COUNT(*) AS total FROM rutina_ejercicios WHERE id_usuario = %s 
    """, (id_usuario,))
    resultado = cursor.fetchone()
    total_ejercicios = resultado['total'] if resultado else 0

    cursor.execute(""" 
        SELECT * FROM misiones 
        WHERE premio_experiencia <= %s 
        AND id_mision NOT IN (SELECT id_mision FROM logros_misiones WHERE id_usuario = %s) 
    """, (total_ejercicios, id_usuario))
    
    misiones_pendientes = cursor.fetchall()

    for mision in misiones_pendientes:
        cursor.execute(""" 
            INSERT INTO logros_misiones (id_usuario, id_mision, fecha_completada) 
            VALUES (%s, %s, NOW()) 
        """, (id_usuario, mision['id_mision']))
        # Si la misión tiene un premio en monedas, añadirlas al usuario
        if mision['premio_moneda'] > 0:
            cursor.execute("UPDATE usuarios SET monedas = monedas + %s WHERE id_usuario = %s", 
                           (mision['premio_moneda'], id_usuario))
        # Si la misión tiene un premio en productos, añadirlo al inventario del usuario
        if mision['premio_producto']:
            # Registrar en la tabla 'compras' como un historial
            cursor.execute("INSERT INTO compras (id_usuario, id_producto, cantidad) VALUES (%s, %s, %s)",
                           (id_usuario, mision['premio_producto'], 1))
            # Actualizar el inventario del usuario
            cursor.execute("SELECT cantidad FROM inventario WHERE id_usuario = %s AND id_producto = %s", 
                           (id_usuario, mision['premio_producto']))
            inventario = cursor.fetchone()
            if inventario:
                cursor.execute("UPDATE inventario SET cantidad = cantidad + 1 WHERE id_usuario = %s AND id_producto = %s",
                               (id_usuario, mision['premio_producto']))
            else:
                cursor.execute("INSERT INTO inventario (id_usuario, id_producto, cantidad) VALUES (%s, %s, %s)",
                               (id_usuario, mision['premio_producto'], 1))
        connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for('missions'))

@app.route('/inventory')
def inventory():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    id_usuario = session['id_usuario']

    # Obtener los productos en el inventario del usuario
    cursor.execute(""" 
        SELECT p.id, p.nombre, p.descripcion, p.precio, p.imagen, i.cantidad
        FROM inventario i 
        JOIN productos p ON i.id_producto = p.id 
        WHERE i.id_usuario = %s 
    """, (id_usuario,))

    products = cursor.fetchall()

    return render_template('inventory.html', products=products)

@app.route('/use_item/<int:producto_id>', methods=['POST'])
def use_item(producto_id):
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    id_usuario = session['id_usuario']

    # Verificar si el producto está en el inventario del usuario
    cursor.execute("SELECT cantidad FROM inventario WHERE id_usuario = %s AND id_producto = %s", (id_usuario, producto_id))
    inventario = cursor.fetchone()

    if not inventario or inventario['cantidad'] <= 0:
        flash("No tienes este producto en tu inventario.")
        return redirect(url_for('inventory'))

    # Obtener información del producto
    cursor.execute("SELECT nombre FROM productos WHERE id = %s", (producto_id,))
    producto = cursor.fetchone()

    # Reducir la cantidad en el inventario
    cursor.execute("UPDATE inventario SET cantidad = cantidad - 1 WHERE id_usuario = %s AND id_producto = %s", (id_usuario, producto_id))
    
    # Eliminar el producto del inventario si la cantidad llega a 0
    cursor.execute("DELETE FROM inventario WHERE id_usuario = %s AND id_producto = %s AND cantidad = 0", (id_usuario, producto_id))
    
    db.commit()

    flash(f"¡Has usado {producto['nombre']} con éxito!")
    return redirect(url_for('inventory'))

@app.route('/profile')
def profile():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (session['id_usuario'],))
    usuario = cursor.fetchone()

    return render_template('profile.html', usuario=usuario)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    Timer(1.25, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    app.run(debug=True, use_reloader=False)