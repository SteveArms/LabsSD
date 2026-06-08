from zeep import Client

# URL del WSDL del servicio SOAP público
WSDL_URL = 'http://www.dneonline.com/calculator.asmx?WSDL'

def conectar_servicio():
    """Crea y retorna el cliente SOAP."""
    print("Conectando al servicio SOAP...")
    client = Client(WSDL_URL)
    print("Conexión exitosa.\n")
    return client

def demostrar_operaciones(client):
    """Ejecuta todas las operaciones disponibles del servicio."""
    print("=" * 50)
    print("  CALCULADORA SOAP - Resultados")
    print("=" * 50)

    # Add
    resultado_add = client.service.Add(5, 8)
    print(f"  Add(5, 8)       = {resultado_add}")

    # Subtract
    resultado_sub = client.service.Subtract(20, 7)
    print(f"  Subtract(20, 7) = {resultado_sub}")

    # Multiply
    resultado_mul = client.service.Multiply(6, 9)
    print(f"  Multiply(6, 9)  = {resultado_mul}")

    # Divide
    resultado_div = client.service.Divide(100, 4)
    print(f"  Divide(100, 4)  = {resultado_div}")

    print("=" * 50)
    print(f"  Resultado esperado Add(5,8): 13")
    print(f"  Resultado obtenido:          {resultado_add}")
    print("=" * 50)

if __name__ == "__main__":
    try:
        client = conectar_servicio()
        demostrar_operaciones(client)
    except Exception as e:
        print(f"Error al conectar con el servicio SOAP: {e}")