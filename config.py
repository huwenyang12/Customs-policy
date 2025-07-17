# 路径配置 & 全局配置
import os

# 通用根路径配置
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "output", "data")
LOG_DIR = os.path.join(BASE_DIR, "output", "logs")

# 文件保存
DOWNLOAD_CZB_DIR = os.path.join(BASE_DIR, "output", "downloads", "czb") # 财政部
DOWNLOAD_SWW_DIR = os.path.join(BASE_DIR, "output", "downloads", "sww") # 商务委
DOWNLOAD_HGFG_DIR = os.path.join(BASE_DIR, "output", "downloads", "hgfg") # 海关法规
DOWNLOAD_ZCJD_DIR = os.path.join(BASE_DIR, "output", "downloads", "zcjd") # 海关法规_政策解读
DOWNLOAD_GXB_DIR = os.path.join(BASE_DIR, "output", "downloads", "gxb") # 工信部
DOWNLOAD_YJJ_DIR = os.path.join(BASE_DIR, "output", "downloads", "hgfg") # 药监局


# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 文件保存
os.makedirs(DOWNLOAD_CZB_DIR, exist_ok=True) # 财政部
os.makedirs(DOWNLOAD_SWW_DIR, exist_ok=True) #商务委
os.makedirs(DOWNLOAD_HGFG_DIR, exist_ok=True) #海关法法规
os.makedirs(DOWNLOAD_ZCJD_DIR, exist_ok=True) #海关法规_政策解读
os.makedirs(DOWNLOAD_GXB_DIR, exist_ok=True) #工信部
os.makedirs(DOWNLOAD_YJJ_DIR, exist_ok=True) #药监局


# 全局参数,设置最大爬取页数
MAX_PAGES_HGFG = 1 # 海关法规
MAX_PAGES_ZCJD = 2 # 海关法规_政策解读
MAX_PAGES_CZB = 1 # 财政部
MAX_PAGES_SWW =1 # 商务委最大爬取页数【固定值=1】
MAX_PAGES_GXB =1 # 工信部最大爬取页数【固定值=1】
MAX_PAGES_YJJ =2 # 药监局
