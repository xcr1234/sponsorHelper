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
    # 参考资料：https://www.msn.cn/zh-cn/news/other/%E8%A7%81%E4%B8%8D%E6%83%AFb%E7%AB%99up%E4%B8%BB%E7%9A%84%E5%B8%A6%E8%B4%A7%E5%B9%BF%E5%91%8A-%E6%95%99%E4%BD%A0%E5%88%A9%E7%94%A8ai%E5%BF%AB%E9%80%9F%E8%B7%B3%E8%BF%87/ar-AA1VCxW4?ocid=msedgdhp&pc=U531&cvid=6983691241084fce9ed37425b24a7dcf&ei=6
    import asyncio
    asyncio.run(main())