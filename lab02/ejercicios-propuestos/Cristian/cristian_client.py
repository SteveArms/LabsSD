import socket
import time

SERVER_HOST = 'localhost'
SERVER_PORT = 12345

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# T0: justo antes de enviar
t0 = int(time.time() * 1000)

# Enviar un mensaje cualquiera para solicitar hora
client_socket.sendto(b'request_time', (SERVER_HOST, SERVER_PORT))

# Recibir respuesta
data, _ = client_socket.recvfrom(1024)
t1 = int(time.time() * 1000)

server_time = int(data.decode())
rtt = t1 - t0
offset = rtt // 2
synced_time = server_time + offset

print(f"T0 (envio)            : {t0}")
print(f"Tiempo del servidor   : {server_time}")
print(f"T1 (recepcion)        : {t1}")
print(f"RTT                   : {rtt} ms")
print(f"Compensacion (RTT/2)  : {offset} ms")
print(f"Hora sincronizada     : {synced_time}")
print(f"Hora local actual     : {int(time.time() * 1000)}")

client_socket.close()