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
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content