import asyncio
import json
import os.path
from typing import Optional

from bilibili_api import Credential, login_v2
from bilibili_api.login_v2 import QrCodeLoginEvents
from loguru import logger

credential: Optional[Credential]

def get_credential() -> Credential:
    if credential is None:
        raise Exception('Credential not initialized.')
    return credential

async def init():
    if os.path.exists('credential.json'):
        with open('credential.json', 'r') as f:
            data = json.load(f)

            sessdata = data['sessdata']
            bili_jct = data['bili_jct']
            ac_time_value = data['ac_time_value']

            tmp = Credential(sessdata=sessdata,
                          bili_jct=bili_jct,
                          ac_time_value=ac_time_value)

            if await tmp.check_valid():
                global credential
                credential = tmp

async def is_valid():
    if credential is None:
        return False
    else:
        return await credential.check_valid()

def save_credential():
    if credential is None:
        raise Exception('Credential not initialized.')
    with open('credential.json', 'w') as f:
        f.write(json.dumps({
            'sessdata': credential.sessdata,
            'bili_jct': credential.bili_jct,
            'ac_time_value': credential.ac_time_value
        }))

async def refresh_credential():
    if credential is None:
        raise Exception('Credential not initialized.')
    try:
        await credential.refresh()
        logger.info("Credential refreshed.")

        save_credential()
    except Exception:
        logger.exception("Failed to refresh credential.")


async def qr_login():
    """二维码登录"""
    # 生成二维码登录实例，平台选择网页端
    qr = login_v2.QrCodeLogin(platform=login_v2.QrCodeLoginChannel.WEB)
    # 生成二维码
    await qr.generate_qrcode()
    logger.info(f'二维码已生成到{qr.get_qrcode_picture().url}，请扫码登录')
    logger.info(f'二维码内容：\n {qr.get_qrcode_terminal()}')

    while True:
        # 每5秒轮询一次
        await asyncio.sleep(5)

        state = await qr.check_state()
        if state == QrCodeLoginEvents.TIMEOUT:
            logger.info('二维码已过期')
            return False
        if state == QrCodeLoginEvents.CONF:
            logger.info('已扫描二维码，请在手机确认登录')
        if state == QrCodeLoginEvents.DONE:
            logger.info('登录成功')
            global credential
            credential = qr.get_credential()
            save_credential()

            return True

async def validate() -> Optional[Credential]:
    if not await is_valid():
        logger.info('credential无效，需要二维码登录获取新的凭证')
        if not await qr_login():
            return None
    elif credential.ac_time_value and await credential.check_refresh():
        logger.info('凭证已过期，刷新凭证')
        await refresh_credential()

    return credential