import requests

token = "9591bca2739d476ea4ef77ce3df5908d"

ids = ['19cf300811f74919ab760af254d69348', 'b6576ecfd64c4e08b69c9f95ed5a3c8f', '84ac7c19af6645cfb11ca3b5325cbc0e', 'cc91604a057843adb5e6b75bcefe8be0', 'eda2f726cd3b4174873496b0c5227ba7', 'd328636296f244feb6060f5a7ea54e53', '05c2659bda434ca2a3b809c0f5360e10', '0086ad23565c4d39bbaaecc0325684ec', 'd364fbb28bb04d7bbd8688138bc0b803']

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