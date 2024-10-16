from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from openai_service.openai_client import OpenAiClient

app = FastAPI(
    title="OpenAIService"
)

openai_client = OpenAiClient()


class PromptSchema(BaseModel):
    content: str
    api_key: Optional[str] = None


@app.post("/prompt/")
async def get_answer(prompt: PromptSchema):
    data = await openai_client.get_answer(content=prompt.content,api_key = prompt.api_key)
    return data
