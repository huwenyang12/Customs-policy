import json
import logging
import os
from customs_policy_client import CustomsPolicyClient

# 初始化客户端
obj = CustomsPolicyClient(token="9591bca2739d476ea4ef77ce3df5908d")

# 所有要处理的 JSON 文件名
file_names = [
    "海关法规.json",
    "政策解读.json",
    "财政部.json",
    "商务委.json",
    "药监局.json",
    "工信部.json"
]

# JSON 文件目录
json_dir = r"D:\海关接口\海关_附件1\output\data"

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"成功读取 {os.path.basename(path)}，共 {len(data)} 条政策数据")
        return data
    except Exception as e:
        print(f"错误：读取 {path} 时发生未知错误 - {str(e)}")
        return []

def process_customs_policies(data_list):
    success_count = 0
    failed_count = 0
    skip_count = 0
    created_ids = []

    for i, policy in enumerate(data_list):
        print(f"\n=== 处理第 {i+1}/{len(data_list)} 条政策 ===")
        print(f"政策标题: {policy['政策标题']}")
        policy_id = policy["唯一ID"]

        if obj.checkout_policy_exists(policy_id):
            print(f"该政策已存在，policyId: {policy_id}，跳过创建")
            skip_count += 1
            continue

        try:
            releaseDate_str = policy["发布时间"]
            effectiveDate_str = policy["生效日期"]
            release_ts = obj.timestamp_ms_str(releaseDate_str)
            effective_ts = obj.timestamp_ms_str(effectiveDate_str)

            zip_path = policy["zip包路径"]
            print(f"正在上传文件: {zip_path}")
            attachment_url = obj.upload_file(zip_path)

            if not attachment_url:
                print("文件上传失败，跳过该政策")
                failed_count += 1
                continue

            title = policy["政策标题"]
            issuing_agency = policy["发文机关"]
            url = policy["详情页链接"]
            document_number = policy["发布文号"]
            validity_status = policy["是否有效"]
            attachment_count = str(policy["zip包文件数量"])

            policy_data = {
                "articleTitle": title,
                "documentIssuingAgency": issuing_agency,
                "articleUrl": url,
                "releaseDate": release_ts,
                "effectiveDate": effective_ts,
                "issueNum": document_number,
                "efficacy": validity_status,
                "attachment": attachment_count,
                "attachmentUrl": attachment_url,
                "policyId": policy_id
            }

            print("文件上传成功，开始创建政策...")
            created_id = obj.create_policy(policy_data)

            if created_id:
                print(f"创建成功，ID: {created_id}")
                created_ids.append(created_id)
                success_count += 1
            else:
                print("创建失败，尝试回滚删除...")
                deleted = obj.delete_policy(created_id)
                if deleted:
                    print("已回滚删除")
                else:
                    print("删除失败，请手动检查")
                failed_count += 1

        except Exception as e:
            print(f"❌ 处理时出错: {str(e)}")
            failed_count += 1

    print(f"\n=== 本批处理完成 ===")
    print(f"成功: {success_count} 条")
    print(f"失败: {failed_count} 条")
    print(f"跳过: {skip_count} 条")
    print(f"总计: {len(data_list)} 条")

    if created_ids:
        logging.info(f"成功创建的政策ID：{created_ids}\n")

# 执行处理（循环所有文件）
if __name__ == "__main__":
    for file_name in file_names:
        print(f"\n\n======= 开始处理文件：{file_name} =======")
        path = os.path.join(json_dir, file_name)
        data = read_file(path)
        if data:
            process_customs_policies(data)
