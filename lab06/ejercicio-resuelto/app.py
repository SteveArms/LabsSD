from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

productos = [
    {"id": 1, "nombre": "Laptop"},
    {"id": 2, "nombre": "Mouse"}
]

@app.route('/productos', methods=['GET'])
def obtener():
    return jsonify(productos)

@app.route('/productos', methods=['POST'])
def agregar():
    data = request.json
    productos.append(data)
    return jsonify({"mensaje":"Producto agregado"}), 201

@app.route('/productos/<int:id>', methods=['DELETE'])
def eliminar(id):
    global productos
    productos = [p for p in productos if p["id"] != id]
    return jsonify({"mensaje":"Producto eliminado"})

if __name__ == '__main__':
    app.run(debug=True)