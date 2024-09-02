from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


class FilesConfig(BaseSettings):
    static_path: str = "static"
    template_path: str = "templates"
    uploads_path: str = "files/uploads"


class AppConfig(BaseSettings):
    title: str = Field(alias="APP_TITLE")
    host: str = Field(alias="APP_HOST")
    port: int = Field(alias="APP_PORT")
    origins: list[str] = Field(alias="APP_ORIGINS")


class Config:
    def __init__(self, env_path: str = "./.env"):
        load_dotenv(env_path)
        self.app = AppConfig()
        self.files = FilesConfig()
