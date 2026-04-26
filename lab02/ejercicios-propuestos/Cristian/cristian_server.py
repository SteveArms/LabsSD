import socket
import time

SERVER_HOST = 'localhost'
SERVER_PORT = 12345

# Crear socket UDP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))
print(f"Servidor de tiempo escuchando en {SERVER_HOST}:{SERVER_PORT}")

while True:
    # Esperar datagrama de cualquier cliente
    data, addr = server_socket.recvfrom(1024)
    # Obtener tiempo actual en milisegundos
    server_time = int(time.time() * 1000)
    # Enviar respuesta
    server_socket.sendto(str(server_time).encode(), addr)
    print(f"Atendida solicitud de {addr}, hora enviada: {server_time}")