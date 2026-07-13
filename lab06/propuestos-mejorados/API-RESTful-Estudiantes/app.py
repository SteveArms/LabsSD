from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from validador import validar_datos_estudiante

app = Flask(__name__)
CORS(app)

estudiantes_db = {}
contador_id = 1

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/style.css')
def serve_css():
    return send_file('style.css')

@app.route('/estudiantes', methods=['GET'])
def listar_estudiantes():
    query = request.args.get('search', '').strip().lower()
    carrera = request.args.get('carrera', '').strip().lower()
    estudiantes = list(estudiantes_db.values())
    
    if query:
        estudiantes = [e for e in estudiantes if query in e['nombre'].lower() or query in e['apellido'].lower() or query in e['cui'].lower()]
    if carrera:
        estudiantes = [e for e in estudiantes if carrera in e['carrera'].lower()]
        
    return jsonify(estudiantes), 200

@app.route('/estudiantes/<int:id>', methods=['GET'])
def obtener_estudiante(id):
    estudiante = estudiantes_db.get(id)
    if estudiante is None:
        return jsonify({"error": "Estudiante no encontrado"}), 404
    return jsonify(estudiante), 200

@app.route('/estudiantes', methods=['POST'])
def registrar_estudiante():
    global contador_id
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No se recibieron datos JSON"}), 400

    error_val = validar_datos_estudiante(datos, estudiantes_db)
    if error_val:
        return jsonify({"error": error_val}), 400

    nuevo = {
        "id": contador_id,
        "nombre": datos["nombre"].strip(),
        "apellido": datos["apellido"].strip(),
        "carrera": datos["carrera"].strip(),
        "cui": datos["cui"].strip().upper()
    }
    estudiantes_db[contador_id] = nuevo
    contador_id += 1
    return jsonify(nuevo), 201

@app.route('/estudiantes/<int:id>', methods=['PUT'])
def actualizar_estudiante(id):
    estudiante = estudiantes_db.get(id)
    if estudiante is None:
        return jsonify({"error": "Estudiante no encontrado"}), 404

    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No se recibieron datos JSON"}), 400

    error_val = validar_datos_estudiante(datos, estudiantes_db, id)
    if error_val:
        return jsonify({"error": error_val}), 400

    actualizado = {
        "id": id,
        "nombre": datos["nombre"].strip(),
        "apellido": datos["apellido"].strip(),
        "carrera": datos["carrera"].strip(),
        "cui": datos["cui"].strip().upper()
    }
    estudiantes_db[id] = actualizado
    return jsonify(actualizado), 200

@app.route('/estudiantes/<int:id>', methods=['DELETE'])
def eliminar_estudiante(id):
    if id not in estudiantes_db:
        return jsonify({"error": "Estudiante no encontrado"}), 404
    del estudiantes_db[id]
    return jsonify({"mensaje": "Estudiante eliminado correctamente"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)