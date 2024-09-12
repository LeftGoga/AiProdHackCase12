from src.services.chat import ChatService
from src.services.files import FileService


class Services:
    def __init__(self):
        self.chat = ChatService()
        self.files = FileService()
