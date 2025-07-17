import requests

token = "9591bca2739d476ea4ef77ce3df5908d"

id = "c82ec484a0644ae4adcf1a9deaeefdc1"

# 接口地址，添加 id 作为查询参数
url = f"http://123.60.179.95:48090/admin-api/cms/policy/delete?id={id}"  # 创建的 id


# 请求头
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 发起 DELETE 请求（无需 json 数据体）
resp = requests.delete(url, headers=headers)

# 打印返回内容
print("状态码:", resp.status_code)
print("响应内容:", resp.text)