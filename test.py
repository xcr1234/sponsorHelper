import pprint

from bilibili_api import video

from src.credential import init, validate


async def main():
    await init()
    credential = await validate()
    v = video.Video("BV1JAFTzeEt9",credential=credential)  # 初始化视频对象
    video_info =  await  v.get_info()
    cid = video_info['pages'][0]['cid']
    res = await v.get_subtitle(cid)
    pprint.pp(res)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())