import json
from typing import List, Literal, Union

import json_repair
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from src.openapi_client import create_request

# 严格保留你要求的 actionType 取值
ActionType = Literal[
    "sponsor",           # 赞助/恰饭
    "selfpromo",         # 无偿/自我推广
    "exclusive_access",  # 独家访问/抢先体验
    "interaction",       # 三连/互动提醒
    "poi_highlight",     # 精彩时刻/重点
    "intro",             # 过场/开场动画
    "outro",             # 鸣谢/结束画面
    "preview",           # 回顾/概要
    "padding",           # 填充内容/前黑/后黑
    "filler",            # 离题闲聊/玩笑
    "music_offtopic"     # 音乐:非音乐部分
]

class VideoSegment(BaseModel):
    start: float = Field(..., description="开始时间戳")
    end: float = Field(..., description="结束时间戳")
    reason: str = Field(..., description="判定理由")
    actionType: ActionType = Field(..., description="广告或片段类型")

class VideoAnalysisResponse(BaseModel):
    segments: List[VideoSegment]

# 提取 JSON Schema 字符串，用于注入 Prompt
JSON_SCHEMA_STR = VideoAnalysisResponse.model_json_schema()

async def get_video_analysis(title: str, subtitle_text: str):
    # 1. 构造包含详细说明的 Prompt
    prompt = f"""
你是一个视频内容分析助手。我会给你一个视频的标题和带有时间戳的字幕内容。
请判断字幕中是否存在与视频主题无关的插播广告或特殊片段。

视频标题：{title}

字幕列表：
{subtitle_text}

【输出要求】
1. 必须返回标准的 JSON 对象。
2. 广告类型 actionType 必须严格从以下列表中选择，不得自行创造：
   - sponsor: 赞助/恰饭
   - selfpromo: 无偿/自我推广
   - exclusive_access: 独家访问/抢先体验
   - interaction: 三连/互动提醒
   - poi_highlight: 精彩时刻/重点
   - intro: 过场/开场动画
   - outro: 鸣谢/结束画面
   - preview: 回顾/概要
   - padding: 填充内容/前黑/后黑
   - filler: 离题闲聊/玩笑
   - music_offtopic: 音乐:非音乐部分
3. 必须严格符合以下 JSON Schema 结构：
{json.dumps(JSON_SCHEMA_STR, ensure_ascii=False, indent=2)}    
4.如果没有任何广告，请返回 {{"segments": []}}。 只输出 JSON，不要有任何其他解释文字。
"""

    logger.debug(f'字幕模式提示词：\n{prompt.replace("\n", "\\n")}')

    history = [{"role": "user", "content": prompt}]

    # --- 第一次尝试 ---
    response_content = await create_request(prompt, history=history)


    validated_res = None
    try:
        # 尝试解析并验证
        raw_json = json_repair.loads(response_content)
        validated_res = VideoAnalysisResponse.model_validate(raw_json)
    except (ValidationError, Exception) as e:
        # 提取具体的错误信息给大模型看
        error_info = str(e) if not isinstance(e, ValidationError) else e.errors()[0]['msg']
        logger.warning(f"首次返回校验不通过: {error_info}")

        # --- 第二次尝试（追问且仅尝试一次） ---
        retry_prompt = f"你上一次返回的 JSON 结构或字段有误（错误：{error_info}）。请检查 actionType 是否超出了给定范围，并严格按照要求的 JSON 结构重新返回结果，不要包含任何 Markdown 代码块或解释。"

        history.append({"role": "assistant", "content": response_content})
        history.append({"role": "user", "content": retry_prompt})

        fixed_content = await create_request(retry_prompt, history=history)

        try:
            fixed_json = json_repair.loads(fixed_content)
            validated_res = VideoAnalysisResponse.model_validate(fixed_json)
        except:
            logger.error("二次修正依然失败，返回空结果。")
            return {"segments": []}

    return validated_res.model_dump()