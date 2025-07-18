import requests
import json
import logging
import os
from typing import Optional
from datetime import datetime


# 获取当前脚本所在目录
base_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(base_dir, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "customs_policy.log")

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

class CustomsPolicyClient:
    def __init__(self, token: str, tenant_id: str = "1"):
        self.token = token
        self.tenant_id = tenant_id
        self.upload_url = "http://123.60.179.95:48082/admin-api/infra/file/upload-info"
        self.create_url = "http://123.60.179.95:48090/admin-api/cms/policy/create"
        self.delete_url = "http://123.60.179.95:48090/admin-api/cms/policy/delete"
        self.select_url = "http://123.60.179.95:48090/admin-api/cms/policy/checkout"


        self.upload_headers = {
            "Authorization": f"Bearer {self.token}",
            "tenant-id": self.tenant_id
        }

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def upload_file(self, file_path: str, upload_path: str = "hgzc") -> Optional[str]:
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                params = {"path": upload_path}
                resp = requests.post(self.upload_url, headers=self.upload_headers, files=files, params=params)

            logging.info(f"上传状态码: {resp.status_code}")
            logging.info(f"上传响应: {resp.text}")

            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {}).get("url")
            else:
                logging.error("上传失败")
                return None
        except Exception as e:
            logging.exception("上传文件出错")
            return None

    def create_policy(self, data: dict) -> Optional[str]:
        try:
            resp = requests.post(self.create_url, headers=self.headers, json=data)
            logging.info(f"创建状态码: {resp.status_code}")
            logging.info(f"创建响应: {resp.text}\n")
            if resp.status_code == 200:
                result = resp.json()
                return result.get("data")  # 这是创建后返回的 ID（可用于删除）
            else:
                logging.error("创建接口响应异常")
                return None
        except Exception as e:
            logging.exception("创建政策出错")
            return None


    def delete_policy(self, policy_id: str) -> bool:
        try:
            url = f"{self.delete_url}?id={policy_id}"
            resp = requests.delete(url, headers=self.headers)
            logging.info(f"删除状态码: {resp.status_code}")
            logging.info(f"删除响应: {resp.text}")
            return resp.status_code == 200
        except Exception as e:
            logging.exception("删除政策出错")
            return False
        
    def timestamp_ms_str(self, date_str: str) -> str:
        try:
            ts = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)
            return str(ts)
        except Exception:
            return ""
    
    def checkout_policy_exists(self, policy_id: str) -> bool:
        """
        检查指定的 policyId 是否已存在。
        返回 True 表示存在，False 表示可以创建。
        """
        data = {"ids": [policy_id]}
        try:
            resp = requests.post(self.select_url, headers=self.headers, json=data, timeout=10)
            resp.raise_for_status()
            res_json = resp.json()
            if res_json.get("code") == 0:
                return policy_id in res_json.get("data", [])
        except Exception as e:
            logging.exception("查重失败:", e)
        return False
