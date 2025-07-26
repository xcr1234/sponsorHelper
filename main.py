import asyncio

from loguru import logger
from src.credential import init as init_credential
from src.db import init as init_db
from src.main import run_once


async def main():
    init_db()
    await init_credential()
    while True:
        try:
            await run_once()
            logger.info('------------------------')
        except Exception as e:
            logger.exception(f'系统执行异常: {e}')

        await asyncio.sleep(30 * 60)


if __name__ == "__main__":
    asyncio.run(main())