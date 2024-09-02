from fastapi import APIRouter, Form
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from src.core.models.message import Message
from src.services.chat import ChatService

messages = []


class ChatRouter(APIRouter):
    def __init__(self, chat_service: ChatService, templates: Jinja2Templates):
        super().__init__(prefix="/chat", tags=["chat"])
        self.chat_service = chat_service
        self.templates = templates
        self.add_api_route("/", self.get_chat, methods=["GET"])
        self.add_api_route("/send", self.send_message, methods=["POST"])

    async def get_chat(self, request: Request):
        return self.templates.TemplateResponse(
            "chat.html", {"request": request, "messages": messages}
        )

    async def send_message(self, text: str = Form(...)):
        message = Message(username="User", text=text)
        messages.append(message)
        return message.model_dump(mode="json")
