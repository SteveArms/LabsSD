import socket
import time

SERVER_HOST = 'localhost'
SERVER_PORT = 12345

# Crear socket UDP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #IPV4, UDP
server_socket.bind((SERVER_HOST, SERVER_PORT)) #vincular a la dirección y puerto
print(f"Servidor de tiempo escuchando en {SERVER_HOST}:{SERVER_PORT}")

while True:
    # Esperar datagrama de cualquier cliente
    data, addr = server_socket.recvfrom(1024) # max 1024 bytes
    # Obtener tiempo actual en milisegundos
    server_time = int(time.time() * 1000) # 1970-01-01T00:00:00Z en ms
    # Enviar respuesta
    server_socket.sendto(str(server_time).encode(), addr) # a bytes UTF-8
    print(f"Atendida solicitud de {addr}, hora enviada: {server_time}")