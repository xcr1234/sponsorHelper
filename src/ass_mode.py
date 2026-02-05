"""使用字幕处理视频广告"""
import pprint

import httpx
import json_repair
from bilibili_api import video
from loguru import logger
from openai import AsyncOpenAI

from src.config import conf, ass_conf
from src.credential import validate
from src.db import insert_commit
from src.process_ad import check_exist
from src.retry import retry


async def get_subtitle_body(subtitle_data):
    """
    从字幕列表中选择最优语言轨道并下载内容
    优先级：中文(ai-zh, zh-CN...) > 其他任何语言
    """
    subtitles = subtitle_data.get('subtitles', [])
    logger.debug(f"字幕获取Data：{subtitle_data}")
    if not subtitles:
        return None

    # 1. 寻找中文字幕轨道
    target = None
    zh_keywords = ['zh', '中文', 'hans', 'hant']
    for sub in subtitles:
        if any(k in sub['lan'].lower() or k in sub['lan_doc'].lower() for k in zh_keywords):
            target = sub
            break

    # 2. 如果没找到中文，取第一个可用的轨道
    if not target:
        target = subtitles[0]

    # 3. 下载字幕内容
    url = target['subtitle_url']
    if url.startswith('//'):
        url = 'https:' + url

    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(url)
        if response.status_code == 200:
            return response.json().get('body', [])
    return None


client = AsyncOpenAI(api_key=ass_conf['api_key'], base_url=ass_conf['base_url'])


async def detect_ads_with_llm(title, subtitle_body):
    """
    调用大模型分析字幕中的广告内容
    """
    # 1. 简化字幕，减少 Token 消耗 (只保留时间戳和内容)
    formatted_subtitles = []
    for item in subtitle_body:
        formatted_subtitles.append(f"[{item['from']} - {item['to']}] {item['content']}")

    subtitle_text = "\n".join(formatted_subtitles)

    # 2. 构造 Prompt
    prompt = f"""
你是一个视频内容分析助手。我会给你一个视频的标题和带有时间戳的字幕内容。
请判断字幕中是否存在与视频主题无关的插播广告（例如：转转回收、得物推广、游戏App、理财产品等）。

视频标题：{title}

字幕列表：
{subtitle_text}

1. 必须返回一个标准的 JSON 对象，格式如下：
```json
{{
  "segments": [
    {{ "start": 秒, "end": 秒, "reason": "理由" }}   //识别出广告开始的时间戳和结束的时间戳。
  ]
}}
```
2. 如果没有任何广告，请返回 {{"segments": []}}。
3. 只输出 JSON，不要有任何其他解释文字。
"""
    logger.debug(f'字幕模式提示词：\n{prompt}')

    response = await client.chat.completions.create(
        model=ass_conf['use_model'],
        messages=[
            {"role": "system", "content": "你是一个专业的视频广告识别专家。请仅返回 JSON 内容。"},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json_repair.loads(response.choices[0].message.content)

http_client = httpx.AsyncClient()
@retry(delay=10)
async def process_video_ass(video_id: str, up_id: int, up_name: str):
    logger.info(f'video id: {video_id}')
    if await check_exist(video_id):
        logger.info(f'视频已经处理过了，跳过.')
        return

    # 1. 获取视频信息
    credential = await validate()
    v = video.Video(bvid=video_id, credential=credential)
    video_info =  await  v.get_info()
    title = video_info['title']

    # 2. 获取字幕
    cid = video_info['pages'][0]['cid']
    raw_subtitle_res = await v.get_subtitle(cid)

    # 3. 下载并解析字幕 Body
    logger.info(f"正在下载视频字幕...")
    body = await get_subtitle_body(raw_subtitle_res)

    if not body:
        logger.info("未找到有效字幕内容。")
        return

    # 4. 调用 AI 识别
    ad_results_llm = await detect_ads_with_llm(title, body)

    logger.debug(f'识别结果： {ad_results_llm}')
    ad_results = ad_results_llm['segments']
    if not ad_results:
        logger.info("未找到广告内容。")
        insert_commit(video_id, {
            'haveAd': False
        }, up_id, up_name)
        return
    sponsor_conf = conf['sponsor']
    payload = {
        'videoID': video_id,
        'userID': sponsor_conf['private_id'],
        'userAgent': sponsor_conf['user_agent'],
        'videoDuration': video_info['pages'][0]['duration'],
        'segments': [
            {
                'segment': [seg['start'], seg['end']], # 映射 AI 的识别结果
                'category': 'sponsor',
                'actionType': 'skip'
            } for seg in ad_results
        ]
    }

    logger.info(f'commit payload: {payload}')
    # 提交片段
    res = await http_client.post(f'{sponsor_conf['api']}/api/skipSegments', json=payload)


    if not res.is_success:
        raise Exception(f'提交片段失败 {res.text}')

    logger.info(f'提交片段成功 {res.text}')

    k = {
        'ad_results': ad_results,
        'haveAd': len(ad_results) > 0
    }
    k.update(payload)
    k['userID'] = '******'
    k['res'] = res.text

    insert_commit(video_id, k, up_id, up_name)
