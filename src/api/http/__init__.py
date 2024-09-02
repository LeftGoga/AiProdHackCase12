from starlette.templating import Jinja2Templates

from src.api.http.v1.chat import ChatRouter
from src.services import Services


class Routers:
    def __init__(self, services: Services, templates: Jinja2Templates):
        self.v1 = [
            ChatRouter(services.chat, templates),
        ]
