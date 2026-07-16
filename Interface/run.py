import json
import logging
import os
from .customs_policy_client import CustomsPolicyClient
from .get_token_cookie import main as query_voucher


# 初始化日志
logging.basicConfig(level=logging.INFO, format="%(message)s")

# 获取token
url, get_token, get_cookie = query_voucher()
# logging.info(f"Request URL: {url}")
# logging.info(f"Authorization: {get_token}")
# logging.info(f"Cookie: {get_cookie}" )

# 初始化客户端
obj = CustomsPolicyClient(token=get_token)
file_names = [
    "海关法规.json",
    "政策解读.json",
    "财政部.json",
    "商务委.json",
    "药监局.json",
    "工信部.json",
]

# 抓取数据路径
json_dir = r"D:\CMS-Client\CustomRate-Sync\Customs-policy-main\output\data"
# json_dir = r"C:\Users\FangYan\Desktop\Customs-policy-main\output\data"


# 所有文件的处理结果（按文件名记录成功/失败）
all_results = {}


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"成功读取 {os.path.basename(path)}，共 {len(data)} 条政策数据")
        return data
    except Exception as e:
        print(f"错误：读取 {path} 时发生未知错误 - {str(e)}")
        return []


def process_customs_policies(file_label, data_list):
    result = {
        "success": [],
        "failed": [],
        "skipped": [],
    }

    for i, policy in enumerate(data_list):
        print(f"\n=== 处理第 {i + 1}/{len(data_list)} 条政策 ===")
        print(f"政策标题: {policy['政策标题']}")
        policy_id = policy["唯一ID"]

        if obj.checkout_policy_exists(policy_id):
            print(f"该政策已存在，policyId: {policy_id}，跳过创建")
            result["skipped"].append(policy_id)
            continue

        try:
            release_ts = obj.timestamp_ms_str(policy["发布时间"])
            effective_ts = obj.timestamp_ms_str(policy["生效日期"])
            zip_path = policy["zip包路径"]

            print(f"正在上传文件: {zip_path}")
            attachment_url = obj.upload_file(zip_path)
            if not attachment_url:
                print("文件上传失败，跳过该政策")
                result["failed"].append(policy_id)
                continue

            policy_data = {
                "articleTitle": policy["政策标题"],
                "documentIssuingAgency": policy["发文机关"],
                "articleUrl": policy["详情页链接"],
                "releaseDate": release_ts,
                "effectiveDate": effective_ts,
                "issueNum": policy["发布文号"],
                "efficacy": policy["是否有效"],
                "attachment": str(policy["zip包文件数量"]),
                "attachmentUrl": attachment_url,
                "policyId": policy_id,
            }

            print("文件上传成功，开始创建政策...")
            created_id = obj.create_policy(policy_data)
            if created_id:
                print(f"创建成功，ID: {created_id}")
                result["success"].append(created_id)
            else:
                print("创建失败，尝试回滚删除...")
                obj.delete_policy(created_id)
                result["failed"].append(policy_id)
        except Exception as e:
            print(f"处理时出错: {str(e)}")
            result["failed"].append(policy_id)

    # 存储结果
    all_results[file_label] = result


def run_interface():
    print("======= 开始批量处理海关政策数据 =======\n")

    for file_name in file_names:
        print(f"\n\n======= 开始处理文件：{file_name} =======")
        path = os.path.join(json_dir, file_name)
        data = read_file(path)
        if data:
            label = os.path.splitext(file_name)[0]
            process_customs_policies(label, data)

    # 汇总统计
    total_success, total_failed, total_skipped, total_policies = 0, 0, 0, 0
    success_ids, failed_ids = [], []

    print("\n\n========== ✅ 总体执行结果 ==========")
    for label, result in all_results.items():
        total_success += len(result["success"])
        total_failed += len(result["failed"])
        total_skipped += len(result["skipped"])
        total_policies += (
            len(result["success"]) + len(result["failed"]) + len(result["skipped"])
        )  # 统计条数
        success_ids.extend(result["success"])
        failed_ids.extend(result["failed"])

    logging.info(f"总共处理政策文件数：{len(file_names)}")
    logging.info(f"总共处理政策条数：{total_policies}")
    logging.info(f"总计成功：{total_success} 条")
    logging.info(f"总计失败：{total_failed} 条")
    logging.info(f"总计跳过：{total_skipped} 条\n")
    logging.info(f"成功政策ID列表：{success_ids}")
    logging.info(f"失败政策policyId列表：{failed_ids}\n")

    print("\n========== 📂 每个文件处理情况 ==========")
    for label, result in all_results.items():
        file_total = (
            len(result["success"]) + len(result["failed"]) + len(result["skipped"])
        )
        logging.info(f"\n📁 文件：{label}")
        logging.info(f"  总处理条数：{file_total}")
        logging.info(f"  成功：{len(result['success'])} 条 → {result['success']}")
        logging.info(f"  失败：{len(result['failed'])} 条 → {result['failed']}")
        logging.info(f"  跳过：{len(result['skipped'])} 条")


if __name__ == "__main__":
    run_interface()
