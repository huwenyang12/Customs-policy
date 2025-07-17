import requests

# 你已有的 token
token = "9591bca2739d476ea4ef77ce3df5908d"

# 接口地址
url = "http://123.60.179.95:48090/admin-api/cms/policy/create"

# 请求头
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 示例数据结构（根据 Swagger 核实并添加 documentIssuingAgency）
data = {
    "articleTitle": "关于进口散装食用植物油贮存运输有关要求的公告",  # 文章标题
    "documentIssuingAgency": "海关总署",  # 发文机关
    "articleUrl": "http://www.customs.gov.cn/customs/302249/302266/302267/6627988/index.html",  #文章链接
    "releaseDate": "2025-07-15 12:27:37",  # 发布日期，添加时间部分
    "effectiveDate": "2025-07-15 12:27:37",  # 生效日期，添加时间部分
    "issueNum": "147",  # 发布文号
    "efficacy": "有效",  # 效力：有效/已废止
    "attachment": "2",  # 附件数量
    "attachmentUrl": "http://example.com/your_file.zip", # zip包下载链接
    "policyId":"hgzc147" # 海关政策唯一标识
}


# 发起 POST 请求
resp = requests.post(url, headers=headers, json=data)

# 打印返回内容
print("状态码:", resp.status_code)
print("响应内容:", resp.text)