from starlette.templating import Jinja2Templates

from src.api.http.v1.chat import ChatRouter
from src.core.config import FilesConfig
from src.services import Services


class Routers:
    def __init__(self, services: Services, files_config: FilesConfig):
        templates = Jinja2Templates(directory=files_config.template_path)
        self.v1 = [
            ChatRouter(services.chat, templates, files_config=files_config),
        ]
