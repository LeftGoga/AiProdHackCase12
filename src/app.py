import logging

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from src.api.http import Routers
from src.core.config import Config
from src.services import Services


class App(FastAPI):
    def __init__(self, config: Config, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config.app
        super().__init__(*args, **kwargs, title=self.config.title)
        self.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.origins,
            allow_methods=["GET", "POST"],
        )
        self.mount(
            "/static", StaticFiles(directory=config.files.static_path), name="static"
        )
        templates = Jinja2Templates(directory=config.files.template_path)
        services = Services()
        routers = Routers(services, templates)
        for router in routers.v1:
            self.include_router(router)

    def run(self):
        uvicorn.run(self, host=self.config.host, port=self.config.port)
