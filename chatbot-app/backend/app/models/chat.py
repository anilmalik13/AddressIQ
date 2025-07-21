from typing import List, Dict

class ChatMessage:
    def __init__(self, sender: str, content: str):
        self.sender = sender
        self.content = content

class Chat:
    def __init__(self):
        self.messages: List[ChatMessage] = []

    def add_message(self, sender: str, content: str):
        message = ChatMessage(sender, content)
        self.messages.append(message)

    def get_messages(self) -> List[Dict[str, str]]:
        return [{"sender": msg.sender, "content": msg.content} for msg in self.messages]