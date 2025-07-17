# 下载、保存、文件名清洗等
import re
import aiohttp
import os
from logger import log_info, log_error

# 清洗文件名称
def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

# 文件下载方法
async def download_file(url, save_path, referer=None):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": referer or "http://gss.mof.gov.cn",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(save_path, 'wb') as f:
                        f.write(await response.read())
                    log_info(f"下载成功: {save_path}")
                else:
                    log_error(f"下载失败（状态码 {response.status}）: {url}")
    except Exception as e:
        log_error(f"下载异常: {url}，错误: {e}")
