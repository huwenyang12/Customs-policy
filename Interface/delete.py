import requests

token = "9591bca2739d476ea4ef77ce3df5908d"

ids = ['e584dad6f3164d878a519b6026148c29', 'ee8367389b2e418fae0e9ae23b01d0a4', '1c046fb5fd6144e4aab621c50365b347', '4a55e37978db432c9319ef872a903a49', '36cc215af0fd469aa786f917647eca21', 'e21594bdc99b4f258a3b1999bbcd5bd7']

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