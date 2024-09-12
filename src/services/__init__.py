from src.core.config import TranslatorConfig
from src.services.ai import AIService


class Services:
    def __init__(self, translator_config: TranslatorConfig):
        self.ai = AIService(translator_config)
