import json

class ChatMessage:
    WHOISIN = 0
    MESSAGE = 1
    LOGOUT = 2

    def __init__(self, msg_type, message):
        self.type = msg_type
        self.message = message

    def to_json(self):
        return json.dumps({"type": self.type, "message": self.message})

    @staticmethod
    def from_json(data):
        obj = json.loads(data)
        return ChatMessage(obj["type"], obj["message"])