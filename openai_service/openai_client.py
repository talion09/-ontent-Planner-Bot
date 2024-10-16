import logging

from openai import OpenAI

from openai_service.config import GPT_API_KEY


class OpenAiClient:

    def __init__(self):
        self.client = OpenAI(
            api_key=GPT_API_KEY,
        )
        self.model = "gpt-3.5-turbo-1106"

    async def get_answer(self, content: str, api_key: str | None):
        try:
            if api_key:
                self.client.api_key = api_key
            else:
                self.client.api_key = GPT_API_KEY

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": content}
                ]
            )
            return {"status": "success", "data": completion.choices[0].message.content, "details": None}
        except Exception as e:
            logging.error(f"chat_gpt {e}")
            return {"status": "error", "data": None, "details": str(e)}
