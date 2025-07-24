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
    def __init__(self, token, tenant_id: str = "1"):
        self.token = token
        self.tenant_id = tenant_id
        self.upload_url = "http://123.60.179.95:48082/admin-api/infra/file/upload-info"
        self.create_url = "http://123.60.179.95:48090/admin-api/cms/policy/create"
        self.delete_url = "http://123.60.179.95:48090/admin-api/cms/policy/delete"
        self.select_url = "http://123.60.179.95:48090/admin-api/cms/policy/checkout"
        self.presign_api = "http://123.60.179.95:48082/admin-api/infra/file/presigned-url"
        self.today = datetime.now().strftime("%Y-%n")
        


        self.upload_headers = {
            "Authorization": f"Bearer {self.token}",
            "tenant-id": self.tenant_id
        }

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }


    def upload_file(self, file_path, upload_path: str = None):
        """
        使用预签名 URL 上传文件，并返回下载地址。
        """
        upload_path = f"/CMS/HGZC/{self.today}"

        try:
            if not os.path.exists(file_path):
                logging.error(f"文件不存在: {file_path}")
                return None

            filename = os.path.basename(file_path)
            full_upload_path = f"{upload_path}/{filename}"

            # Step 1: 获取预签名 URL
            res = requests.get(self.presign_api, headers=self.upload_headers, params={"path": full_upload_path})
            logging.info(f"获取预签名响应状态: {res.status_code}")
            if res.status_code != 200:
                logging.error(f"获取预签名失败，响应内容: {res.text}")
                return None

            res_json = res.json()
            data = res_json.get("data")
            if not data:
                logging.error(f"获取预签名失败：{res_json.get('msg', '未知错误')}")
                return None

            upload_url = data.get("uploadUrl")
            download_url = data.get("url")

            if not upload_url or not download_url:
                logging.error("返回的数据缺少 uploadUrl 或 url")
                return None

            # Step 2: 上传文件到 OSS
            with open(file_path, "rb") as f:
                upload_res = requests.put(upload_url, data=f)

            logging.info(f"上传文件响应状态码: {upload_res.status_code}")
            if upload_res.status_code == 200:
                logging.info(f"上传成功，下载地址: {download_url}")
                return download_url
            else:
                logging.error(f"上传失败，响应内容: {upload_res.text}")
                return None

        except Exception as e:
            logging.exception("上传过程中发生异常")
            return None


    def create_policy(self, data):
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


    def delete_policy(self, policy_id):
        try:
            url = f"{self.delete_url}?id={policy_id}"
            resp = requests.delete(url, headers=self.headers)
            logging.info(f"删除状态码: {resp.status_code}")
            logging.info(f"删除响应: {resp.text}")
            return resp.status_code == 200
        except Exception as e:
            logging.exception("删除政策出错")
            return False
        
    def timestamp_ms_str(self, date_str):
        try:
            ts = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)
            return str(ts)
        except Exception:
            return ""
    
    def checkout_policy_exists(self, policy_id):
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
