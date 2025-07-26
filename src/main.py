from bilibili_api import dynamic
from bilibili_api.dynamic import DynamicType
from loguru import logger

from src.credential import get_credential, is_valid, refresh_credential, qr_login
from src.process_ad import process_video
from src.utils import is_near


async def run_once():
    if not await is_valid():
        logger.info('credential无效，需要二维码登录获取新的凭证')
        if not await qr_login():
            return
    elif get_credential().ac_time_value and await get_credential().check_refresh():
        logger.info('凭证已过期，刷新凭证')
        await refresh_credential()

    # 处理视频广告逻辑  拉取自己的动态
    result = await dynamic.get_dynamic_page_info(get_credential(), DynamicType.VIDEO)

    items = result['items']

    video_list = [x for x in items if x['type'] == 'DYNAMIC_TYPE_AV' and is_near(x)]

    if len(video_list) == 0:
        logger.info('没有新视频')

    for video in video_list:
        video_id = video['modules']['module_dynamic']['major']['archive']['bvid']
        user_id = video['modules']['module_author']['mid']
        up_name = video['modules']['module_author']['name']

        await process_video(video_id, user_id, up_name)
