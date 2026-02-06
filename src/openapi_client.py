from loguru import logger
from openai import AsyncOpenAI

from src.config import conf

ass_conf = conf['ass']
client = AsyncOpenAI(api_key=ass_conf['api_key'], base_url=ass_conf['base_url'])

async def create_request(prompt: str, history=None):
    """
    支持流式打印内容并返回完整回复
    history: 用于存储对话上下文，便于追问
    """
    if history is None:
        history = [{"role": "user", "content": prompt}]

    response = await client.chat.completions.create(
        model=ass_conf['use_model'],
        messages=history,
        response_format={"type": "json_object"},
        stream=True,  # 开启流式传输
        max_tokens=4096,
        extra_body={
            "thinking_budget": 1024,
            "enable_thinking": True,
        },
        temperature=0.6,
        top_p=0.95,
    )

    full_content = ""
    print("--- 模型思考中 ---")

    async for chunk in response:
        delta = chunk.choices[0].delta

        # 1. 处理思考过程 (Reasoning Content)
        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
            print(delta.reasoning_content, end="", flush=True)

        # 2. 处理正式内容 (Content)
        if hasattr(delta, 'content') and delta.content:
            # 如果是刚开始输出正文，换个行
            if not full_content:
                print("\n\n--- 最终回答 ---")
            print(delta.content, end="", flush=True)
            full_content += delta.content

    print("\n" + "-"*20)
    return full_content