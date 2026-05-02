import socket
import threading
import sys
from chat_message import ChatMessage

class Client:
    def __init__(self, server, port, username):
        self.server = server
        self.port = port
        self.username = username
        self.socket = None
        self.notif = " *** "

    def display(self, msg):
        print(msg)

    def send_message(self, chat_msg):
        try:
            self.socket.sendall(chat_msg.to_json().encode())
        except:
            pass

    def disconnect(self):
        if self.socket:
            self.socket.close()

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server, self.port))
        except Exception as e:
            self.display(f"Error connecting to server: {e}")
            return False
        self.display(f"Connection accepted {self.socket.getpeername()}")
        self.socket.sendall(self.username.encode())
        threading.Thread(target=self.listen_from_server, daemon=True).start()
        return True

    def listen_from_server(self):
        while True:
            try:
                data = self.socket.recv(4096).decode()
                if not data:
                    break
                print(data, end="")
                print("> ", end="", flush=True)
            except:
                break
        self.display(f"{self.notif}Server has closed the connection{self.notif}")
        self.disconnect()

def main():
    port = 1500
    server_addr = "localhost"
    username = "Anonymous"

    if len(sys.argv) >= 2:
        username = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
        except:
            print("Invalid port number")
            return
    if len(sys.argv) >= 4:
        server_addr = sys.argv[3]

    client = Client(server_addr, port, username)
    if not client.start():
        return

    print("\nHello! Welcome to the chatroom.")
    print("Instructions:")
    print("1. Simply type the message to send broadcast to all active clients")
    print("2. Type '@username<space>yourmessage' to send a private message")
    print("3. Type 'WHOISIN' to see list of active clients")
    print("4. Type 'LOGOUT' to logoff from server")

    while True:
        print("> ", end="", flush=True)
        msg = sys.stdin.readline().strip()
        if not msg:
            continue
        if msg.upper() == "LOGOUT":
            client.send_message(ChatMessage(ChatMessage.LOGOUT, ""))
            break
        elif msg.upper() == "WHOISIN":
            client.send_message(ChatMessage(ChatMessage.WHOISIN, ""))
        else:
            client.send_message(ChatMessage(ChatMessage.MESSAGE, msg))
    client.disconnect()

if __name__ == "__main__":
    main()