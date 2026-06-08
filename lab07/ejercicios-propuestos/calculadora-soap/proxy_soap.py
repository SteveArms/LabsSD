import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from zeep import Client
from zeep.exceptions import Fault

# Sirve los archivos estáticos desde la misma carpeta del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR)
CORS(app)

WSDL_URL = 'http://www.dneonline.com/calculator.asmx?WSDL'
_client  = None

def get_client():
    global _client
    if _client is None:
        _client = Client(WSDL_URL)
    return _client

# ── Sirve el HTML en la raíz ──────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'calculadora_soap.html')

# ── API SOAP proxy ────────────────────────────────────────────────
@app.route('/soap', methods=['POST'])
def soap_proxy():
    data = request.get_json()
    op   = data.get('operation')
    a    = int(data.get('a', 0))
    b    = int(data.get('b', 0))

    try:
        c = get_client()
        ops = {
            'Add'     : lambda: c.service.Add(a, b),
            'Subtract': lambda: c.service.Subtract(a, b),
            'Multiply': lambda: c.service.Multiply(a, b),
            'Divide'  : lambda: c.service.Divide(a, b),
        }
        if op not in ops:
            return jsonify({'error': f'Operación desconocida: {op}'}), 400

        resultado = ops[op]()
        return jsonify({'result': resultado, 'operation': op, 'a': a, 'b': b})

    except Fault as e:
        return jsonify({'error': f'SOAP Fault: {e.message}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Status ────────────────────────────────────────────────────────
@app.route('/status', methods=['GET'])
def status():
    try:
        get_client()
        return jsonify({'status': 'online', 'wsdl': WSDL_URL})
    except Exception as e:
        return jsonify({'status': 'offline', 'error': str(e)}), 503

if __name__ == '__main__':
    print("=" * 55)
    print("  Proxy SOAP activo")
    print("  Abre en tu navegador: http://localhost:5000")
    print("=" * 55)
    app.run(host='127.0.0.1', port=5000, debug=False)