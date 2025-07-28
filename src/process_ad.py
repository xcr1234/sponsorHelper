import asyncio
import os
import tempfile

import httpx
from bilibili_api import video, HEADERS
from google.genai import types
from loguru import logger
from pydantic import BaseModel

from src.config import sponsor_conf, get_google_client, running_conf, gemini_conf
from src.db import commit_exists, insert_commit
from src.retry import retry

http_client = httpx.AsyncClient()


async def check_exist(video_id : str):
    found = commit_exists(video_id)
    if found:
        return True

    res = await http_client.get(f'{sponsor_conf['api']}/api/skipSegments?videoID={video_id}&category=sponsor')
    if res.status_code == 404:
        return False
    if res.is_success:
        return True
    return False

class AdModel(BaseModel):
    haveAd: bool
    beginTime: int
    endTime: int

@retry(delay=10)
async def process_video(video_id: str, up_id: int, up_name: str):
    logger.info(f'video id: {video_id}')
    if await check_exist(video_id):
        logger.info(f'it has been processed, skip')
        return

    v = video.Video(bvid=video_id)
    video_info =  await  v.get_info()

    duration = video_info['pages'][0]['duration']
    if duration < running_conf['min_second'] or duration > running_conf['max_second']:
        logger.info(f'video duration {duration} is too long or too short, skip')
        return

    file = await download_file(video_id, video_info)

    google_client = get_google_client()

    logger.info('begin upload')
    myfile = await google_client.aio.files.upload(file=file)
    logger.info(f'upload file done')

    while myfile.state.name == "PROCESSING":
        logger.info('PROCESSING')
        await asyncio.sleep(10)
        myfile = await google_client.aio.files.get(name=myfile.name)

    if myfile.state.name == "FAILED":
        logger.error(f'处理文件失败 {myfile}')
        raise ValueError(myfile.state.name)

    logger.info('begin generate content')

    prompt = """
1.请帮我判断这个视频，判断是否中间是否有与视频内容无关的广告内容，如果是返回
haveAd: true
beginTime: 广告的开始时间（秒）
endTime: 广告的结束时间（秒）
3.如果不包含广告，则返回
haveAd: false
beginTime: 0
endTime: 0
"""
    response = await google_client.aio.models.generate_content(
        model=gemini_conf['model'], contents=[myfile, prompt],
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            response_schema=AdModel
        )
    )

    logger.info(response.text)

    ad_result: AdModel = response.parsed

    if not ad_result.haveAd:
        logger.info('no ad found')
        insert_commit(video_id, ad_result.model_dump(), up_id, up_name)
        return

    if await check_exist(video_id):
        logger.info(f'it has been processed, skip')
        return

    payload =  {
        'videoID': video_id,
        'userID': sponsor_conf['private_id'],
        'userAgent': sponsor_conf['user_agent'],
        'videoDuration': video_info['pages'][0]['duration'],
        'segments': [
            {
                'segment': [ad_result.beginTime, ad_result.endTime],
                'category': 'sponsor',
                'actionType': 'skip'
            }
        ]
    }
    logger.info(f'commit payload: {payload}')
    # 提交片段
    res = await http_client.post(f'{sponsor_conf['api']}/api/skipSegments', json=payload)

    if not res.is_success:
        logger.error(f'提交片段失败 {res.text}')

    logger.info(f'提交片段成功 {res.text}')

    k = ad_result.model_dump()
    k.update(payload)
    k['userID'] = '******'
    k['res'] = res.text

    insert_commit(video_id, k, up_id, up_name)


async def download_file(video_id: str, video_info):
    cid = video_info['pages'][0]['cid']
    res2 = await http_client.get(f'https://api.bilibili.com/x/player/playurl?bvid={video_id}&cid={cid}', headers=HEADERS)

    logger.info(f"video url result : {res2.text}")
    res2.raise_for_status()
    res2_json = res2.json()
    if res2_json['code'] != 0:
        raise Exception('获取播放地址失败')

    url =  res2_json['data']['durl'][0]['url']
    logger.info(f"video download url : {url}")

    file = await download_url_to_file(url)

    logger.info(f"file path : {file}")

    # 获取file的文件大小
    file_size = os.path.getsize(file)
    file_size_kb = round(file_size / 1024, 2)


    if file_size_kb > 1024:
        file_size_str = f'{round( file_size_kb / 1024, 2)}MB'
    else:
        file_size_str = f'{file_size_kb}KB'

    logger.info(f'video file {file}, file size: {file_size_str}')

    return file


async def download_url_to_file(url):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as f:
        async with http_client.stream("GET", url, headers=HEADERS) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                f.write(chunk)
        return f.name