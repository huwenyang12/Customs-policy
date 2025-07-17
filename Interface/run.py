from customs_policy_client import CustomsPolicyClient

client = CustomsPolicyClient(token="9591bca2739d476ea4ef77ce3df5908d")

# 上传文件
file_name = "压缩1.zip"
zip_path = rf"D:\海关接口\海关_附件1\Interface\zip_package\{file_name}"
download_url = client.upload_file(zip_path)

if download_url:
    policy_data = {
        "id": "108516",
        "articleTitle": "关于进口散装食用植物油贮存运输有关要求的公告",
        "documentIssuingAgency": "海关总署",
        "articleUrl": "http://www.customs.gov.cn/customs/302249/302266/302267/6627988/index.html",
        "releaseDate": "2025-07-17T10:58:02.708Z",
        "effectiveDate": "2025-07-17T10:58:02.708Z",
        "issueNum": "147",
        "efficacy": "有效",
        "attachment": "1",
        "attachmentUrl": download_url,
        "policyId": "1001",
        # "createTime":"2025-07-17T10:58:02.708Z"
    }

    # 创建政策，获取返回的 ID（删除用）
    created_id = client.create_policy(policy_data)

    if created_id:
        print(f"创建成功，ID: {created_id}")
    else:
        print("创建失败，尝试删除刚创建的政策")

        # 回滚失败删除（如果失败发生在逻辑后半段你也可以传一个你预设的 policyId）
        deleted = client.delete_policy(created_id)
        if deleted:
            print("创建失败后已自动删除该政策")
        else:
            print("创建失败但删除失败，请手动处理")
else:
    print("上传失败，取消创建")