from loguru import logger
from openai import AsyncOpenAI

from src.config import conf

ass_conf = conf['ass']
client = AsyncOpenAI(api_key=ass_conf['api_key'], base_url=ass_conf['base_url'])

async def create_request(prompt: str):
    response = await client.chat.completions.create(
        model=ass_conf['use_model'],
        messages=[
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        stream=False,
        max_tokens=4096,
        extra_body={
            "thinking_budget": 1024
        },
        temperature=0.6,
        top_p=0.95,
        enable_thinking=True
    )

    reasoning_content = response.choices[0].message.reasoning_content

    logger.debug(f'reasoning_content:\n{reasoning_content}')

    return response.choices[0].message.content