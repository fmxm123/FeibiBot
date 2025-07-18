from nonebot.log import logger
from pathlib import Path
from typing import Union, Optional
import httpx
import aiofiles

class ResourceError(Exception):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return self.msg

async def download_url(url: str) -> Union[httpx.Response, None]:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                resp = await client.get(url, timeout=20)
                if resp.status_code != 200:
                    continue
                return resp
            except Exception:
                logger.warning(f"Error occurred when downloading {url}, retry: {i+1}/3")
    
    logger.warning(f"Abort downloading")
    return None

async def download_resource(resource_dir: Path, name: str, _type: Optional[str] = None) -> bool:
    '''
    下载行为被禁用，避免阻塞插件加载
    '''
    logger.warning(f"[资源跳过] 已禁止自动下载资源 {name}，请手动放置在：{resource_dir}")
    return False  # 或者 raise ResourceError(f"缺少资源 {name}")

async def save_resource(resource_dir: Path, response: httpx.Response) -> None:
    async with aiofiles.open(resource_dir, "wb") as f:
        await f.write(response.content)
