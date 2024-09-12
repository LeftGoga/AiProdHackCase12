import requests
import json


class YandexTranslator:
    def __init__(
        self,
        api_key="AQVN0XyMgY6NL_bWEWsBxiH5TBGTxzRqsrWkjSEg",
        api_id="ajehfi6833kd5vrdc4bb",
        folder_id="b1gjj01i0f670l2o8hrs",
        target_language="ru",
    ):
        self.api_key = api_key
        self.api_id = api_id
        self.folder_id = folder_id
        self.target_language = target_language

    def translate(self, text):
        body = {
            "targetLanguageCode": self.target_language,
            "texts": [text],
            "folderId": self.folder_id,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Api-Key {0}".format(self.api_key),
        }

        response = requests.post(
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            json=body,
            headers=headers,
        )

        return json.loads(response.text)["translations"][0]["text"]
