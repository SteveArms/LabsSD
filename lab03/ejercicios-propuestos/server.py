import socket
import threading
import json
from datetime import datetime
from chat_message import ChatMessage

class Server:
    def __init__(self, port=1500):
        self.port = port
        self.clients = []          # lista de dicts: {socket, username, addr}
        self.keep_going = True
        self.notif = " *** "

    # message can be broadcast to all or sent privately to a specific user
    def broadcast(self, message, sender_socket=None, private_target=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"{timestamp} {message}\n"
        if private_target:
            for c in self.clients:
                if c["username"] == private_target:
                    try:
                        c["socket"].sendall(full_msg.encode()) # sent to bytes UTF-8
                    except:
                        self.remove_client(c["socket"])
                    return True
            return False
        else:
            print(full_msg, end="")
            for c in self.clients:
                if sender_socket and c["socket"] == sender_socket:
                    continue
                try:
                    c["socket"].sendall(full_msg.encode()) # sent to bytes UTF-8
                except:
                    self.remove_client(c["socket"])
            return True

    def remove_client(self, sock):
        for i, c in enumerate(self.clients):
            if c["socket"] == sock:
                username = c["username"]
                self.clients.pop(i)
                self.broadcast(f"{self.notif}{username} has left the chat room.{self.notif}")
                break

    # manage communication with a single client
    def handle_client(self, sock, addr):
        try:
            username = sock.recv(1024).decode() # receive username as UTF-8 string
        except:
            return
        with threading.Lock():
            self.clients.append({"socket": sock, "username": username, "addr": addr})
        self.broadcast(f"{self.notif}{username} has joined the chat room.{self.notif}")
        print(f"Nuevo cliente: {username} ({addr})")
        while True:
            try:
                data = sock.recv(4096).decode()
                if not data:
                    break
                msg = ChatMessage.from_json(data) # convert from JSON to ChatMessage object
                if msg.type == ChatMessage.LOGOUT:
                    break
                elif msg.type == ChatMessage.WHOISIN:
                    user_list = f"List of users connected at {datetime.now().strftime('%H:%M:%S')}\n"
                    for i, c in enumerate(self.clients):
                        user_list += f"{i+1}) {c['username']} since {c['addr'][0]}\n"
                    sock.sendall(user_list.encode())
                elif msg.type == ChatMessage.MESSAGE:
                    text = msg.message
                    if text.startswith('@'):
                        parts = text.split(' ', 1)
                        if len(parts) == 2 and parts[0][1:]:
                            target = parts[0][1:]
                            priv_msg = f"[Private] {username}: {parts[1]}"
                            if not self.broadcast(priv_msg, private_target=target):
                                sock.sendall(f"{self.notif}Sorry. No such user exists.{self.notif}\n".encode())
                        else:
                            sock.sendall(f"{self.notif}Use: @username message{self.notif}\n".encode())
                    else:
                        self.broadcast(f"{username}: {text}")
            except:
                break
        self.remove_client(sock)
        sock.close()

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('', self.port))
        server_socket.listen(5) # max 5 pending connections
        print(f"Servidor escuchando en el puerto {self.port}")
        while self.keep_going:
            try:
                client_sock, addr = server_socket.accept() # blocking call
                thread = threading.Thread(target=self.handle_client, args=(client_sock, addr)) # manage client in new thread
                thread.daemon = True
                thread.start()
            except:
                break
        server_socket.close()

    def stop(self):
        self.keep_going = False
        # create a dummy connection to unblock the accept() call
        try:
            s = socket.socket()
            s.connect(('localhost', self.port))
            s.close()
        except:
            pass

if __name__ == "__main__":
    import sys
    port = 1500
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    srv = Server(port)
    srv.start()