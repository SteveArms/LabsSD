import json

class ChatMessage:
    # Tipos de mensaje
    WHOISIN = 0
    MESSAGE = 1
    LOGOUT = 2

    def __init__(self, msg_type, message):
        self.type = msg_type
        self.message = message

    def to_json(self):
        # convierte el mensaje a formato JSON para enviar por la red
        return json.dumps({"type": self.type, "message": self.message})

    @staticmethod
    def from_json(data):
        obj = json.loads(data)
        return ChatMessage(obj["type"], obj["message"])