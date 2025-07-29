import requests

token = "9591bca2739d476ea4ef77ce3df5908d"

ids = ['23a5aaa05e3e4dd0b477702629669975', '52864fe678cb4f3b940670373e7ba64d', '90edc78d81f24301a80e51c7b80a9413', 'b29ddf6e8413455d8723f9c6bdca1b5e', '926f5f8afbab4ed08285d682a4d0a5a0', 'c30503c2d5ba4d4281b7b860de7c2a39']

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