import datetime
import tempfile

import httpx
from bilibili_api import HEADERS

http_client = httpx.AsyncClient()

def is_near(item):
    pub_ts = item['modules']['module_author']['pub_ts']

    # 创建上海时区对象
    tz_shanghai = datetime.timezone(datetime.timedelta(hours=8))

    # 将时间戳转换为上海时区的datetime对象
    pub_time = datetime.datetime.fromtimestamp(pub_ts, tz_shanghai)

    # 获取当前时间并转换为上海时区
    now_shanghai = datetime.datetime.now(tz_shanghai)

    # 计算时间差（两者都是上海时区）
    time_diff = (now_shanghai - pub_time).total_seconds()

    # 检查是否是新发布的视频，并预留一点缓冲时间
    return time_diff < 1.5 * 30 * 60

async def download_video(url):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as f:
        async with http_client.stream("GET", url, headers=HEADERS) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                f.write(chunk)
        return f.name
