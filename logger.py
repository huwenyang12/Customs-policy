# logger.py（统一日志版本）

import logging
import os
from config import LOG_DIR

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件路径（统一）
LOG_FILE = os.path.join(LOG_DIR, "all.log")

# 创建日志记录器
main_logger = logging.getLogger("main_logger")
main_logger.setLevel(logging.INFO)

# 日志格式
formatter = logging.Formatter(
    fmt="%(asctime)s     %(message)s",
    datefmt="%Y-%m-%d %H:%M"
)

# 文件处理器
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)

# 控制台处理器
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# 添加处理器
main_logger.addHandler(file_handler)
main_logger.addHandler(stream_handler)

# 日志函数
def log_info(msg):
    main_logger.info(msg)

def log_error(msg):
    main_logger.error(msg)
