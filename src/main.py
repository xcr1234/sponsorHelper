from bilibili_api import dynamic
from bilibili_api.dynamic import DynamicType
from loguru import logger

from src.credential import validate
from src.process_ad import process_video
from src.utils import is_near


async def run_per_loop():
    credential = await validate()
    if not credential:
        return
    # 处理视频广告逻辑  拉取自己的动态
    result = await dynamic.get_dynamic_page_info(credential, DynamicType.VIDEO)

    items = result['items']

    video_list = [x for x in items if x['type'] == 'DYNAMIC_TYPE_AV' and is_near(x)]

    if len(video_list) == 0:
        logger.info('没有新视频')

    for video in video_list:
        video_id = video['modules']['module_dynamic']['major']['archive']['bvid']
        user_id = video['modules']['module_author']['mid']
        up_name = video['modules']['module_author']['name']

        try:
            await process_video(video_id, user_id, up_name)
        except Exception as e:
            logger.exception(f'处理视频{video_id}出错： {e}')
