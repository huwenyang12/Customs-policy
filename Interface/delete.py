import requests

token = "9591bca2739d476ea4ef77ce3df5908d"

ids = ['7bf997d3d6144ee1a46f963c50118439', 'e1291d9fe43a41e3b4b96bc3d5748382', '86374a81cfb242f1a6ad69ceb929b637', '8eeb7a4e19f14bedaffc9f9ece39e7e9', 'bf6b1474076a46b6b7526ec15fd9739d', '71c621ad404b4a279d093b8d31f9cf86', '00aa9796f7524b01970533186079501d', 'e9135a213ded4db0afed7c219e8c6abf', 'fde11acff02d45f888513bb4bcf419c8', '06f8e21e05014ecc85d6def2ff972d22']

for id in ids:
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